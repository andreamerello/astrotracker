#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

#define RCC_LED RCC_GPIOC
#define PIN_LED GPIO13
#define PORT_LED GPIOC

int main(void) {
        rcc_periph_clock_enable(RCC_LED);
	gpio_set_mode(PORT_LED, GPIO_MODE_OUTPUT_2_MHZ, GPIO_CNF_OUTPUT_PUSHPULL, PIN_LED);
	gpio_set(PORT_LED, PIN_LED);

	while(1) {
		/* wait a little bit */
		for (int i = 0; i < 10000000; i++) {
			__asm__("nop");
		}
		gpio_toggle(PORT_LED, PIN_LED);
	}
}
