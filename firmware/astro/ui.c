#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/exti.h>
#include <libopencm3/cm3/nvic.h>

#include "FreeRTOS.h"
#include "queue.h"
#include "ui.h"
#include "motor.h"
#include "task.h"
#include "mcuio.h"

typedef struct {
	uint32_t port;
	uint32_t pin;
	uint32_t rcc;
	uint32_t exti;
} button_t;

typedef struct {
	int on_ms;
	int off_ms;
} led_blinking_t;

/* these GPIO have internal pull-downs */
static button_t BUTTON_PLAY    = { GPIOA, GPIO4, RCC_GPIOA, EXTI4 };
static button_t BUTTON_STOP    = { GPIOA, GPIO5, RCC_GPIOA, EXTI5 };
static button_t BUTTON_REWIND  = { GPIOA, GPIO6, RCC_GPIOA, EXTI6 };
static button_t BUTTON_FAST_FW = { GPIOA, GPIO8, RCC_GPIOA, EXTI8 };

static QueueHandle_t led_queue;

static void button_init(button_t btn)
{
	rcc_periph_clock_enable(btn.rcc);
	gpio_set_mode(btn.port, GPIO_MODE_INPUT, GPIO_CNF_INPUT_PULL_UPDOWN, btn.pin);
	exti_select_source(btn.exti, btn.port);
	exti_set_trigger(btn.exti, EXTI_TRIGGER_RISING);
	exti_enable_request(btn.exti);
}

void exti4_isr(void)
{
	if (exti_get_flag_status(BUTTON_PLAY.exti)) {
		motor_cmd_from_isr('s');
		exti_reset_request(BUTTON_PLAY.exti);
	}
}

void exti9_5_isr(void)
{
	if (exti_get_flag_status(BUTTON_STOP.exti)) {
		motor_cmd_from_isr('t');
		exti_reset_request(BUTTON_STOP.exti);
	}
	if (exti_get_flag_status(BUTTON_REWIND.exti)) {
		motor_cmd_from_isr('r');
		exti_reset_request(BUTTON_REWIND.exti);
	}
	if (exti_get_flag_status(BUTTON_FAST_FW.exti)) {
		motor_cmd_from_isr('f');
		exti_reset_request(BUTTON_FAST_FW.exti);
	}
}

void set_led_blink(int on_ms, int off_ms)
{
	led_blinking_t c = {on_ms, off_ms};
	xQueueOverwrite(led_queue, &c);
}

void set_led_on(void)
{
	set_led_blink(1000, 0);
}

void set_led_off(void)
{
	set_led_blink(0, 1000);
}

static void led_task(void *arg __attribute((unused)))
{
	TickType_t on_ticks;
	TickType_t off_ticks;
	led_blinking_t periods = {0, 1000}; /* by default the led is off */

	void set_ticks(void)
	{
		on_ticks = periods.on_ms / portTICK_PERIOD_MS;
		off_ticks = periods.off_ms / portTICK_PERIOD_MS;
	}
	set_ticks();

	while (1) {
		gpio_clear(GPIOC, GPIO13);
		if (pdPASS == xQueueReceive(led_queue, &periods, on_ticks)) {
			/* someone set a blink command, reset&continue */
			set_ticks();
			continue;
		}
		gpio_set(GPIOC, GPIO13);
		if (pdPASS == xQueueReceive(led_queue, &periods, off_ticks)) {
			/* someone set a blink command, reset&continue */
			set_ticks();
			continue;
		}

	}
}

void led_init(void)
{
	rcc_periph_clock_enable(RCC_GPIOC);
	gpio_set_mode(GPIOC, GPIO_MODE_OUTPUT_2_MHZ, GPIO_CNF_OUTPUT_OPENDRAIN, GPIO13);
	gpio_clear(GPIOC, GPIO13);
}

void ui_init(void)
{
	led_init();
	button_init(BUTTON_STOP);
	button_init(BUTTON_PLAY);
	button_init(BUTTON_REWIND);
	button_init(BUTTON_FAST_FW);
	rcc_periph_clock_enable(RCC_AFIO);	 // EXTI
	nvic_enable_irq(NVIC_EXTI4_IRQ);
	nvic_enable_irq(NVIC_EXTI9_5_IRQ);
	led_queue = xQueueCreate(1, sizeof(led_blinking_t));
	xTaskCreate(led_task, "led", 128, NULL, 1, NULL);
}
