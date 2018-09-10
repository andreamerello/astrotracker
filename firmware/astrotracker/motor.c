#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#include "motor.h"
#include "tinyprintf.h"

#define ARRAY_SIZE(x) ((int)(sizeof(x) / sizeof((x)[0])))

struct {
	uint32_t port;
	uint32_t pin;
	uint32_t rcc;
} motor_gpio_table[] = {
	{ GPIOA, GPIO0, RCC_GPIOA },
	{ GPIOA, GPIO1, RCC_GPIOA },
	{ GPIOA, GPIO2, RCC_GPIOA },
	{ GPIOA, GPIO3, RCC_GPIOA },
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

static int motor_i = 0;
static int motor_value = 0;

void motor_test(void)
{
	printf("setting pin %d to %d\r\n", motor_i, motor_value);
	set_pin(motor_i, motor_value);
	motor_i += 1;
	if (motor_i == ARRAY_SIZE(motor_gpio_table)) {
		motor_i = 0;
		motor_value = !motor_value;
	}
}
