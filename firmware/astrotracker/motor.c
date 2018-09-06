#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#include "motor.h"

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

void motor_init(void)
{
	int i;
	for (i = 0; i < ARRAY_SIZE(motor_gpio_table); i++) {
		rcc_periph_clock_enable(motor_gpio_table[i].rcc);
		gpio_set_mode(motor_gpio_table[i].pin, GPIO_MODE_OUTPUT_2_MHZ,
			      GPIO_CNF_OUTPUT_PUSHPULL, motor_gpio_table[i].port);
		gpio_clear(motor_gpio_table[i].port, motor_gpio_table[i].pin);
	}

}
