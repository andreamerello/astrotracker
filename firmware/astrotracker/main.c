#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <stdio.h>
#include <errno.h>

#include "cdcacm.h"
#include "tinyprintf.h"

#define RCC_LED RCC_GPIOC
#define PIN_LED GPIO13
#define PORT_LED GPIOC

static usbd_device *usb_dev;

int _write(int file, char *ptr, int len);
void _putc(void *a, char c);


int _write(int file, char *ptr, int len)
{
	int i;

	if (file == 1) {
		cdcacm_tx(ptr, len);
		return i;
	}

	errno = EIO;
	return -1;
}

void _putc(void *a, char c)
{
	(void)a;
	_write(1, &c, 1);
}

int main(void) {
	rcc_clock_setup_in_hsi_out_48mhz();

        rcc_periph_clock_enable(RCC_LED);
	gpio_set_mode(PORT_LED, GPIO_MODE_OUTPUT_2_MHZ,
		      GPIO_CNF_OUTPUT_PUSHPULL, PIN_LED);
	gpio_set(PORT_LED, PIN_LED);


	usb_dev = cdcacm_init();
	/* for tinyprintf */
	init_printf(NULL, _putc);
	//cdcacm_register_rx_cb(echo);

	while(1) {
		usbd_poll(usb_dev);
		/* /\* wait a little bit *\/ */
		/* for (int i = 0; i < 10000000; i++) { */
		/* 	__asm__("nop"); */
		/* } */
		/* gpio_toggle(PORT_LED, PIN_LED); */
	}
}
