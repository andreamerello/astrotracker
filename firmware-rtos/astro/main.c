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



/*
 * Monitor routine
 */
static void monitor(void)
{
	std_printf("Tick %d\n", xTaskGetTickCount());
	vTaskDelay(1000 / portTICK_PERIOD_MS);
}

static void monitor_task(void *arg __attribute((unused))) {

	for (;;)
		monitor();
}


static void motor_task(void *arg __attribute((unused)))
{
	while(1) {
		//motor_step(-1);
		vTaskDelay(50 / portTICK_PERIOD_MS);
	}
}



#if 0
void usb_tapu_strong()
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

void usb_tapu_polite()
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

	rcc_periph_clock_enable(RCC_GPIOC);
	gpio_set_mode(GPIOC,GPIO_MODE_OUTPUT_50_MHZ,GPIO_CNF_OUTPUT_PUSHPULL,GPIO13);
	motor_init();

	xTaskCreate(monitor_task,"monitor",350,NULL,1,NULL);
	xTaskCreate(motor_task,"motor",350,NULL,1,NULL);

	usb_start(1,1);
	gpio_clear(GPIOC,GPIO13);
	std_set_device(mcu_usb);			// Use USB for std I/O

	vTaskStartScheduler();
	for (;;);
}

/* End main.c */
