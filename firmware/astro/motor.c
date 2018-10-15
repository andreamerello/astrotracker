#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#include "FreeRTOS.h"
#include "queue.h"
#include "motor.h"
#include "task.h"

#include "mcuio.h"
#include "rtc.h"

#define TICKS_PER_SECOND 32768UL
#define SIDERAL_DAY (86164UL * TICKS_PER_SECOND)
#define STEPS_FOR_TEN_DEGREES 19955UL
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

static void motor_stop()
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

typedef enum { STOPPED, TRACKING, REWINDING } motor_state_t;

static void motor_task(void *arg __attribute((unused)))
{
	motor_state_t state = STOPPED;
	int direction = 0;
	int step_count = 0;

	void set_state(int _state, int _direction)
	{
		state = _state;
		direction = _direction;
		step_count = 0;
		motor_stop();
		rtc_reset();
	}

	while(1) {
		char cmd;
		TickType_t delay = (state != STOPPED) ? 1 : portMAX_DELAY;
		if (pdPASS == xQueueReceive(motor_queue, &cmd, delay)) {
			switch (cmd) {
			case 'r':
				/* rewind */
				std_printf("Rewinding..\n");
				set_state(REWINDING, 1);
				break;
			case 's':
				/* start */
				std_printf("Starting..\n");
				set_state(TRACKING, -1);
				break;
			case 't':
				/* stop */
				std_printf("Stopping..\n");
				set_state(STOPPED, 0);
				break;
			case '0':
			case '1':
			case '2':
			case '3':
				std_printf("set motor pin %d\n", (cmd - '0'));
				set_pin(cmd - '0', 1);
				break;
			default:
				std_printf("Have a beer.. %c\n", cmd);
				break;
			}
		}

		if (state != STOPPED) {
			uint32_t ticks = rtc_get_ticks();
			uint32_t tick_for_next_step;
			if (state == TRACKING)
				tick_for_next_step = time_for_step(step_count + 1);
			else
				// 130 is a magic number which we found by experimenting, it's
				// the maximum speed the motor can handle
				tick_for_next_step = step_count * 130;

			if (ticks >= tick_for_next_step) {
				std_printf("step %lu, motor_index=%d\n", step_count, motor_current_index);
				motor_step(direction);
				step_count++;
			}
		}
	}
}
