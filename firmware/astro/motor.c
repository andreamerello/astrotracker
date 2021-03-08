#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#include "FreeRTOS.h"
#include "queue.h"
#include "motor.h"
#include "task.h"

#include "mcuio.h"
#include "rtc.h"
#include "ui.h"

/* constants for astro-track velocity */
#define TICKS_PER_SECOND 32768UL
#define SIDERAL_DAY (86164UL * TICKS_PER_SECOND)

static int motor_absolute_position;
static int motor_default_direction = DEFAULT_DIRECTION;

static uint32_t time_for_step(int step)
{
	/*
	 * We use 64bit arithmetic to ensure that the intermediate results don't
	 * overflow.
	 */
	uint64_t step64 = step;
	return step64 * SIDERAL_DAY / (STEPS_FOR_360_DEGREES);
}

#define ARRAY_SIZE(x) ((int)(sizeof(x) / sizeof((x)[0])))

static pin_t MOTOR_GPIO_TABLE[] = MOTOR_PINS;

#if defined(MOTOR_BIPOLAR)
static uint8_t magic_table[][4] = {
//  A1 A2 B1 B2
	{1, 0, 1, 0},
	{0, 0, 1, 0},
	{0, 1, 1, 0},
	{0, 1, 0, 0},
	{0, 1, 0, 1},
	{0, 0, 0, 1},
	{1, 0, 0, 1},
	{1, 0, 0, 0},
};
#elif defined(MOTOR_UNIPOLAR)
static uint8_t magic_table[][4] = {
//  A1 A2 B1 B2
	{1, 0, 0, 0},
	{1, 1, 0, 0},
	{0, 1, 0, 0},
	{0, 1, 1, 0},
	{0, 0, 1, 0},
	{0, 0, 1, 1},
	{0, 0, 0, 1},
	{1, 0, 0, 1},
};
#else
#  error "You must define either MOTOR_UNIPOLAR or MOTOR_BIPOLAR"
#endif


static void motor_task(void *);

static QueueHandle_t motor_queue;

#ifdef BARN_DOOR
static int homing_switch_pressed(void)
{
	return gpio_get(HOMING_PORT, HOMING_PIN);
}
#endif

int motor_toggle_default_direction(void)
{
	motor_default_direction *= -1;
	return motor_default_direction;
}

static void motor_toggle_pin(int i)
{
	uint32_t port = MOTOR_GPIO_TABLE[i].port;
	uint32_t pin = MOTOR_GPIO_TABLE[i].pin;
	gpio_toggle(port, pin);
}


static void motor_set_pin(int i, int value)
{
	uint32_t port = MOTOR_GPIO_TABLE[i].port;
	uint32_t pin = MOTOR_GPIO_TABLE[i].pin;
	if (value)
		gpio_set(port, pin);
	else
		gpio_clear(port, pin);
}

void motor_init(void)
{
	int i;

#ifdef BARN_DOOR
	/* initialize homing switch pin */
	rcc_periph_clock_enable(HOMING_RCC);
	gpio_set_mode(HOMING_PORT, GPIO_MODE_INPUT,
		      GPIO_CNF_INPUT_PULL_UPDOWN, HOMING_PIN);
#endif // BARN_DOOR


	/* initialize motor control pins */
	for (i = 0; i < ARRAY_SIZE(MOTOR_GPIO_TABLE); i++) {
		rcc_periph_clock_enable(MOTOR_GPIO_TABLE[i].rcc);
		gpio_set_mode(MOTOR_GPIO_TABLE[i].port, GPIO_MODE_OUTPUT_2_MHZ,
					  GPIO_CNF_OUTPUT_PUSHPULL, MOTOR_GPIO_TABLE[i].pin);
		gpio_clear(MOTOR_GPIO_TABLE[i].port, MOTOR_GPIO_TABLE[i].pin);
	}

	motor_queue = xQueueCreate(4, sizeof(char));
	xTaskCreate(motor_task, "motor", 350, NULL, 2, NULL);
}

static int motor_current_index = 0;
static void motor_step(int direction)
{
	direction *= motor_default_direction;
	motor_current_index += direction;
	if (motor_current_index == -1)
		motor_current_index = ARRAY_SIZE(magic_table) - 1;
	else if (motor_current_index == ARRAY_SIZE(magic_table))
		motor_current_index = 0;

	for (int i = 0; i < 4; i++) {
		int value = magic_table[motor_current_index][i];
		motor_set_pin(i, value);
	}
}

static void motor_stop(void)
{
	for (int i = 0; i < 4; i++)
		motor_set_pin(i, 0);
}

__maybe_unused static void motor_test(void)
{
	static int motor_i = 0;
	static int motor_value = 0;
	my_printf("setting pin %d to %d\r\n", motor_i, motor_value);
	motor_set_pin(motor_i, motor_value);
	motor_i += 1;
	if (motor_i == ARRAY_SIZE(MOTOR_GPIO_TABLE)) {
		motor_i = 0;
		motor_value = !motor_value;
	}
}

void motor_cmd(char c)
{
	xQueueSend(motor_queue, &c, portMAX_DELAY);
}

/*
void motor_cmd_from_isr(char c)
{
	ui_beep(30, -1);
	xQueueSendFromISR(motor_queue, &c, NULL);
}
*/

static void motor_debug_do_steps(int direction, int n)
{
	int print_speed = 1;
	if (n > 100)
		print_speed = 10;
	if (n > 1000)
		print_speed = 100;

	if (n > 10) {
		const char *s_dir = (direction == 1) ? "forward" : "backward";
		my_printf("Doing %d steps %s\n", n, s_dir);
	}

	motor_stop();
	for(int step=0; step<n; step++) {
		int should_print = (step % print_speed == 0);
		if (should_print)
			my_printf("Step %d", step);
		for(int i=0; i<ARRAY_SIZE(magic_table); i++) {
			if (should_print)
				my_printf(".");
			motor_step(direction);
			vTaskDelay(1 / portTICK_PERIOD_MS); // 3?
		}
		if (should_print)
			my_printf("\n");
	}
	motor_stop();
	motor_absolute_position += (n*direction);
	my_printf("Absolute position: %d\n", motor_absolute_position);
}

typedef enum {
	STOP,
	PLAY,
	FAST_FW,
#ifdef BARN_DOOR
	REWIND,
	HOMING_FOUND,
	HOMING_PRESSED,
	QUITTING_HOME
#endif
} motor_state_t;

static void motor_task(void *arg __attribute((unused)))
{
	motor_state_t state = STOP;
	int direction = 0;
	int step_count = 0;

	void print_state(__maybe_unused const char* msg) {
		my_printf("%s... [abs position: %d]\n", msg, motor_absolute_position);
	}

	bool set_state(int _state)
	{
		if (state == _state)
			return false;
		state = _state;
		switch (state) {
		case PLAY:
			direction = 1;
			set_led_blink(20, 2000, 5);
			break;
		case FAST_FW:
			direction = 1;
			set_led_blink(40, 400, 5);
			break;
		case STOP:
			direction = 0;
			set_led_on();
			break;
#ifdef BARN_DOOR
		case HOMING_PRESSED:
		case QUITTING_HOME:
		case HOMING_FOUND:
			direction = 1;
			break;
		case REWIND:
			direction = -1;
			set_led_blink(400, 40, 0);
			break;
#endif
		}
		step_count = 0;
		motor_stop();
		rtc_reset();
		return true;
	}

	/* while(1) { */
	/*     my_printf("button: %d\n", homing_switch_pressed()); */
	/*     vTaskDelay(300); */
	/* } */
	/* return; */

	/* WARNING: if you want to control the motor with the USB keyboard, you
	 * need to uncomment the lines in main.c:monitor_task */
	while(1) {
		char cmd;
		TickType_t delay = (state != STOP) ? 1 : portMAX_DELAY;
		if (pdPASS == xQueueReceive(motor_queue, &cmd, delay)) {
			switch (cmd) {
			case 'p':
				if (set_state(PLAY))
					print_state("Play");
				break;
			case 't':
				if (set_state(STOP))
					print_state("Stop");
				break;
			case 'f':
				if (set_state(FAST_FW))
					print_state("Fast forward");
				break;

#ifdef BARN_DOOR
			case 'r':
				if (set_state(REWIND))
					print_state("Rewind");
				break;
#endif

#ifdef ENABLE_DEBUG_MOTOR_COMMANDS
			case '0':
			case '1':
			case '2':
			case '3':
				my_printf("toggle motor pin %d\n", (cmd - '0'));
				motor_toggle_pin(cmd - '0');
				break;
			case 'q':
				// full rotation of the motor
				motor_debug_do_steps(1, 512);
				break;
			case 'w':
				// full rotation of the tracker
				motor_debug_do_steps(1, STEPS_FOR_360_DEGREES/8);
				break;
			// forward
			case 'z': motor_debug_do_steps( 1,       1); break;
			case 'x': motor_debug_do_steps( 1,      10); break;
			case 'c': motor_debug_do_steps( 1,     100); break;
			case 'v': motor_debug_do_steps( 1,    1000); break;
			case 'b': motor_debug_do_steps( 1,   10000); break;
			case 'n': motor_debug_do_steps( 1,   30000); break;
			case 'm': motor_debug_do_steps( 1, STEPS_FOR_360_DEGREES/64); break; // 45deg
			// backward
			case 'Z': motor_debug_do_steps(-1,       1); break;
			case 'X': motor_debug_do_steps(-1,      10); break;
			case 'C': motor_debug_do_steps(-1,     100); break;
			case 'V': motor_debug_do_steps(-1,    1000); break;
			case 'B': motor_debug_do_steps(-1,   10000); break;
			case 'N': motor_debug_do_steps(-1,   30000); break;
			case 'M': motor_debug_do_steps(-1, STEPS_FOR_360_DEGREES/64); break;
#endif
			default:
				my_printf("Invalid command: %c\n", cmd);
				break;
			}
		}

#ifdef BARN_DOOR
		if (state == REWIND) {
			/* moving backward looking for switch pressed event */
			if (homing_switch_pressed()) {
				print_state("Homing Pressed");
				set_state(HOMING_PRESSED);
			}
		}

		if (state == HOMING_PRESSED) {
			/* moving forward looking for switch released event */
			if (!homing_switch_pressed()) {
				motor_absolute_position = -HOME_QUIT_STEPS;
				print_state("Quitting Home");
				set_state(QUITTING_HOME);
			}
		}

		if (state == QUITTING_HOME) {
			if (motor_absolute_position == 0) {
				print_state("Homing completed");
				ui_beep(1000, 500);
				set_state(STOP);
			}
		}
#endif

		if (state != STOP) {
			uint32_t ticks = rtc_get_ticks();
			uint32_t tick_for_next_step;

#ifdef BARN_DOOR
			if (direction == 1) {
				if (motor_absolute_position > MOTOR_MAX_POSITION) {
					ui_beep(3000, 150);
					set_state(STOP);
				}
			}
#endif

			if (state == PLAY)
				tick_for_next_step = time_for_step(step_count + 1);
			else
				tick_for_next_step = step_count * FF_TICKS_PER_STEP;

			if (ticks >= tick_for_next_step) {
				motor_step(direction);
				step_count++;
				motor_absolute_position += direction;
			}
		}
	}
}
