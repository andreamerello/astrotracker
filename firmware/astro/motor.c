#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#include "FreeRTOS.h"
#include "queue.h"
#include "motor.h"
#include "task.h"

#include "mcuio.h"
#include "rtc.h"

#define STEPS_FOR_TEN_DEGREES 19955UL

/* constants for astro-track velocity */
#define TICKS_PER_SECOND 32768UL
#define SIDERAL_DAY (86164UL * TICKS_PER_SECOND)


#define MOTOR_MAX_POSITION ((int)STEPS_FOR_TEN_DEGREES * 2)
#define HOME_QUIT_STEPS ((int)STEPS_FOR_TEN_DEGREES / 10)

#define HOMING_PIN GPIO15
#define HOMING_PORT GPIOA
#define HOMING_RCC RCC_GPIOA

static int motor_absolute_position;

static uint32_t time_for_step(int step)
{
	/*
	 * We use 64bit arithmetic to ensure that the intermediate results don't
	 * overflow.
	 */
	uint64_t step64 = step;
	return step64 * SIDERAL_DAY / (36*STEPS_FOR_TEN_DEGREES);
}

#define ARRAY_SIZE(x) ((int)(sizeof(x) / sizeof((x)[0])))

static struct {
	uint32_t port;
	uint32_t pin;
	uint32_t rcc;
} motor_gpio_table[] = {
	{ GPIOA, GPIO1, RCC_GPIOA }, // A1
	{ GPIOA, GPIO3, RCC_GPIOA }, // A2
	{ GPIOA, GPIO0, RCC_GPIOA }, // B1
	{ GPIOA, GPIO2, RCC_GPIOA }, // B2
};

static uint8_t magic_table[][4] = {
	{1, 0, 1, 0},
	{0, 0, 1, 0},
	{0, 1, 1, 0},
	{0, 1, 0, 0},
	{0, 1, 0, 1},
	{0, 0, 0, 1},
	{1, 0, 0, 1},
	{1, 0, 0, 0},
};

static void motor_task(void *);

static QueueHandle_t motor_queue;

static int homing_switch_pressed(void)
{
    return gpio_get(HOMING_PORT, HOMING_PIN);
}

static void set_pin(int i, int value)
{
	uint32_t port = motor_gpio_table[i].port;
	uint32_t pin = motor_gpio_table[i].pin;
	if (value)
		gpio_set(port, pin);
	else
		gpio_clear(port, pin);
}

void motor_init(void)
{
	int i;

    /* initialize homing switch pin */
    rcc_periph_clock_enable(HOMING_RCC);
    gpio_set_mode(HOMING_PORT, GPIO_MODE_INPUT,
                  GPIO_CNF_INPUT_PULL_UPDOWN, HOMING_PIN);

    
    /* initialize motor control pins */
	for (i = 0; i < ARRAY_SIZE(motor_gpio_table); i++) {
		rcc_periph_clock_enable(motor_gpio_table[i].rcc);
		gpio_set_mode(motor_gpio_table[i].port, GPIO_MODE_OUTPUT_2_MHZ,
				  GPIO_CNF_OUTPUT_PUSHPULL, motor_gpio_table[i].pin);
		gpio_clear(motor_gpio_table[i].port, motor_gpio_table[i].pin);
	}

	motor_queue = xQueueCreate(4, sizeof(char));
	xTaskCreate(motor_task, "motor", 350, NULL, 1, NULL);
}

static int motor_current_index = 0;
static void motor_step(int direction)
{
	motor_current_index += direction;
	if (motor_current_index == -1)
		motor_current_index = ARRAY_SIZE(magic_table) - 1;
	else if (motor_current_index == ARRAY_SIZE(magic_table))
		motor_current_index = 0;

	for (int i = 0; i < 4; i++) {
		int value = magic_table[motor_current_index][i];
		set_pin(i, value);
	}
}

static void motor_stop(void)
{
	for (int i = 0; i < 4; i++)
		set_pin(i, 0);
}

static void motor_test(void)
{
	static int motor_i = 0;
	static int motor_value = 0;
	std_printf("setting pin %d to %d\r\n", motor_i, motor_value);
	set_pin(motor_i, motor_value);
	motor_i += 1;
	if (motor_i == ARRAY_SIZE(motor_gpio_table)) {
		motor_i = 0;
		motor_value = !motor_value;
	}
}

void motor_cmd(char c)
{
	xQueueSend(motor_queue, &c, portMAX_DELAY);
}

void motor_cmd_from_isr(char c)
{
	xQueueSendFromISR(motor_queue, &c, NULL);
}

typedef enum {
    STOP,
    PLAY,
    REWIND,
    FAST_FW,
    HOMING_FOUND,
    HOMING_PRESSED,
    QUITTING_HOME
} motor_state_t;

static void motor_task(void *arg __attribute((unused)))
{
	motor_state_t state = STOP;
	int direction = 0;
	int step_count = 0;

	void set_state(int _state)
	{
		if (state == _state)
			return;
		state = _state;
        switch (state) {
        case PLAY:
        case FAST_FW:
        case HOMING_PRESSED:
        case QUITTING_HOME:
        case HOMING_FOUND:
            direction = 1;
            break;
        case STOP:
            direction = 0;
            break;
        case REWIND:
            direction = -1;
            break;
        }
		step_count = 0;
		motor_stop();
		rtc_reset();
	}
    
	while(1) {
		char cmd;
		TickType_t delay = (state != STOP) ? 1 : portMAX_DELAY;
		if (pdPASS == xQueueReceive(motor_queue, &cmd, delay)) {
			switch (cmd) {
			case 'r':
				std_printf("Rewind..\n");
				set_state(REWIND);
				break;
			case 's':
				std_printf("Play..\n");
				set_state(PLAY);
				break;
			case 't':
				std_printf("Stop..\n");
				set_state(STOP);
				break;
			case 'f':
				std_printf("Fast forward..\n");
                set_state(FAST_FW);
				break;
			/* case '0': */
			/* case '1': */
			/* case '2': */
			/* case '3': */
			/* 	std_printf("set motor pin %d\n", (cmd - '0')); */
			/* 	set_pin(cmd - '0', 1); */
			/* 	break; */
			default:
				std_printf("Have a beer.. %c\n", cmd);
				break;
			}
		}

        if (state == REWIND) {
            /* moving backward looking for switch pressed event */
            if (homing_switch_pressed()) {
                std_printf("Homing switch pressed..\n");
                set_state(HOMING_PRESSED);
            }
        }
        
        if (state == HOMING_PRESSED) {
            /* moving forward looking for switch released event */
            if (!homing_switch_pressed()) {
                motor_absolute_position = -HOME_QUIT_STEPS;
                std_printf("Found home, moving slightly away..\n");
                set_state(QUITTING_HOME);
            }
        }

        if (state == QUITTING_HOME) {
            if (motor_absolute_position == 0) {
                std_printf("Homing completed..\n");
                set_state(STOP);
            }
        }

		if (state != STOP) {
			uint32_t ticks = rtc_get_ticks();
			uint32_t tick_for_next_step;

            if (direction == 1) {
                if (motor_absolute_position > MOTOR_MAX_POSITION)
                    set_state(STOP);
            }                
           
			if (state == PLAY)
				tick_for_next_step = time_for_step(step_count + 1);
			else
				// 130 is a magic number which we found by experimenting, it's
				// the maximum speed the motor can handle
				tick_for_next_step = step_count * 130;

			if (ticks >= tick_for_next_step) {
				//std_printf("step %lu, motor_index=%d\n", step_count, motor_current_index);
				motor_step(direction);
				step_count++;
                motor_absolute_position += direction;
			}
		}
	}
}
