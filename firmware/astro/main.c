/* CDC Demo, using the usbcdc library
 * Warren W. Gay VE3WWG
 * Wed Mar 15 21:56:50 2017
 *
 * This demo consists of a text menu driven app, to display
 * STM32F103 registers (STM32F103C8T6 register set assumed).
 */
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <ctype.h>

#include <libopencm3/cm3/cortex.h>
#include <libopencm3/cm3/scb.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/cm3/scb.h>
#include <libopencm3/stm32/rtc.h>
#include <libopencm3/stm32/f1/nvic.h>

#include "mcuio.h"
#include "miniprintf.h"

#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"

#include "motor.h"
#include "ui.h"
#include "rtc.h"


/*
 * There is a bug in the usb layer. If a print is done before the
 * tty is attached then weird thing happen: printed chars are
 * echoed back in stdin..
 * The workaround is not to print before we get an input from tty
 */
static void monitor_task(void *arg __attribute((unused)))
{
	vTaskDelay(2000 / portTICK_PERIOD_MS);
	while (1) {
        // the USB input is not reliable, comment out by default
        /* char c; */
		/* c = std_getc(); */
		/* motor_cmd(c); */
		vTaskDelay(1000);
	}
}

#if 0
static void usb_tapu_strong(void)
{
	int i;

	/*
	 * HACK to force the HOST to re-initialize USB upon a uC reset/reflash
	 * Apparently durig uC reset, the USB lines stay to some electrical
	 * level that does not make the host notice anything.
	 * Forcing USB GPIO to a crazy state for a while makes the magic..
	 */
	rcc_periph_clock_enable(RCC_GPIOA);
	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_OUTPUT_PUSHPULL,GPIO12);
	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_OUTPUT_PUSHPULL,GPIO11);
	gpio_clear(GPIOA, GPIO12);
	gpio_clear(GPIOA, GPIO13);

	for (i = 0; i < 10000; i++)
		__asm__("nop");

	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_INPUT_FLOAT,GPIO12);
	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_INPUT_FLOAT,GPIO11);
}
#endif

static void usb_tapu_polite(void)
{
	int i;

	/*
	 * HACK to force the HOST to re-initialize USB upon a uC reset/reflash
	 * Apparently durig uC reset, the USB lines stay to some electrical
	 * level that does not make the host notice anything.
	 * Forcing USB GPIO to a crazy state for a while makes the magic..
	 */
	rcc_periph_clock_enable(RCC_GPIOA);
	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_INPUT_PULL_UPDOWN,GPIO12);
	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_INPUT_PULL_UPDOWN,GPIO11);
	gpio_clear(GPIOA, GPIO12);
	gpio_clear(GPIOA, GPIO13);

	for (i = 0; i < 10000; i++)
		__asm__("nop");

	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_INPUT_FLOAT,GPIO12);
	gpio_set_mode(GPIOA,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_INPUT_FLOAT,GPIO11);
}

/*
 * Main program: Device initialization etc.
 */
int main(void)
{
	usb_tapu_polite();
	rcc_clock_setup_in_hse_8mhz_out_72mhz();	// Use this for "blue pill"
	rtc_init();
	motor_init();
	ui_init();

	xTaskCreate(monitor_task,"monitor",512,NULL,1,NULL);

	usb_start(1,1);
	std_set_device(mcu_usb);			// Use USB for std I/O

	set_led_blink(500, 500, 0);
	vTaskStartScheduler();
	for (;;);
}

/* End main.c */
