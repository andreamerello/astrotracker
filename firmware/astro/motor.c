#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#include "FreeRTOS.h"
#include "queue.h"
#include "motor.h"
#include "task.h"

#include "mcuio.h"

/* seconds */
#define SIDERAL_DAY 86164

/* degrees/second */
#define ROTATIONAL_SPEED (360.0 / SIDERAL_DAY)

/* number of steps, measured using transparent angles */
#define STEPS_FOR_TEN_DEGREES 19955
#define STEP_FOR_ONE_DEGREE (STEPS_FOR_TEN_DEGREES / 10.0)
#define DEGREES_PER_STEP (1.0 / STEP_FOR_ONE_DEGREE)

/* seconds */
#define DELAY_BETWEEN_STEPS (DEGREES_PER_STEP / ROTATIONAL_SPEED)


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
static void fake_rtc_task(void *);
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
	xTaskCreate(fake_rtc_task, "fake_rtc", 350, NULL, 1, NULL);
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

static void fake_rtc_task(void *arg __attribute((unused)))
{
	while(1) {
		vTaskDelay(1);
		motor_cmd('x');
	}
}

const int slow_speed = 20;
const int fast_speed = 5;

static void motor_task(void *arg __attribute((unused)))
{
	char cmd;
	int count;
	int speed;
	bool running = false;
	int direction = 0;

	void set_speed(int _speed)
	{
		speed = _speed;
		count = 0;
	}

	while(1) {
		if (pdPASS == xQueueReceive(motor_queue, &cmd, portMAX_DELAY)) {
			switch (cmd) {
			case 'r':
				/* rewind */
				std_printf("Rewinding..\n");
				direction = 1;
				set_speed(fast_speed);
				break;
			case 's':
				/* start */
				std_printf("Starting..\n");
				direction = -1;
				set_speed(slow_speed);
				break;
			case 't':
				/* stop */
				std_printf("Stopping..\n");
				direction = 0;
				break;
			case 'x':
				count++;
				break;
			default:
				std_printf("Have a beer.. %c\n", cmd);
				break;
			}
		}

		running = (direction != 0);
		if (running) {
			if (count == speed) {
				count = 0;
				motor_step(direction);
			}
		}
	}
}
