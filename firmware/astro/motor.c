#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#include "motor.h"
#include "miniprintf.h"

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
}

static int motor_current_index = 0;
void motor_step(int direction)
{
	motor_current_index += direction;
	if (motor_current_index == -1)
		motor_current_index = ARRAY_SIZE(magic_table) - 1;
	else if (motor_current_index == ARRAY_SIZE(magic_table))
		motor_current_index = 0;

	for(int i = 0; i < 4; i++) {
		int value = magic_table[motor_current_index][i];
		set_pin(i, value);
	}
}

void motor_test(void)
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
