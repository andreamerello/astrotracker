#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/exti.h>
#include <libopencm3/cm3/nvic.h>
#include <libopencm3/stm32/timer.h>
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
	int beep_rate;
} led_blinking_t;

typedef struct {
	int duration_ms;
	int tone;
	beep_scale_t scale;
} beep_t;

/* these GPIO have internal pull-downs */
static button_t BUTTON_PLAY    = { GPIOA, GPIO4, RCC_GPIOA, EXTI4 };
static button_t BUTTON_STOP    = { GPIOA, GPIO5, RCC_GPIOA, EXTI5 };
static button_t BUTTON_REWIND  = { GPIOA, GPIO6, RCC_GPIOA, EXTI6 };
static button_t BUTTON_FAST_FW = { GPIOA, GPIO8, RCC_GPIOA, EXTI8 };

#define ANTIBUMP_DELAY 1000

static QueueHandle_t led_queue;
static QueueHandle_t buzzer_queue;
static int button_last_interrupt_time = 0;

static void button_init(button_t btn)
{
	rcc_periph_clock_enable(btn.rcc);
	gpio_set_mode(btn.port, GPIO_MODE_INPUT, GPIO_CNF_INPUT_PULL_UPDOWN, btn.pin);
	//exti_select_source(btn.exti, btn.port);
	//exti_set_trigger(btn.exti, EXTI_TRIGGER_RISING);
	//exti_enable_request(btn.exti);
}

static int ui_antibump(void)
{
	int time = timer_get_counter(TIM2);
	if (time < button_last_interrupt_time)
		button_last_interrupt_time -= 65536;


	if (time < (button_last_interrupt_time + ANTIBUMP_DELAY)) {
		return 1;
	} else {
		button_last_interrupt_time = time;
		return 0;
	}
}

/*
void exti4_isr(void)
{
	if (ui_antibump())
		return;

	if (exti_get_flag_status(BUTTON_PLAY.exti)) {
		motor_cmd_from_isr('a'); // "auto"
		exti_reset_request(BUTTON_PLAY.exti);
	}
}

void exti9_5_isr(void)
{
	if (ui_antibump())
		return;

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
*/

/* every beep_rate blinks, we do a beep. If beep_rate == 0, no beeps */
void set_led_blink(int on_ms, int off_ms, int beep_rate)
{
	if (LED_IS_INVERTED) {
		int tmp = on_ms;
		on_ms = off_ms;
		off_ms = tmp;
	}
	led_blinking_t c = {on_ms, off_ms, beep_rate};
	xQueueOverwrite(led_queue, &c);
}

void set_led_on(void)
{
	set_led_blink(1000, 0, 0);
}

void set_led_off(void)
{
	set_led_blink(0, 1000, 0);
}

static void led_task(void *arg __attribute((unused)))
{
	TickType_t on_ticks;
	TickType_t off_ticks;
	int beep_rate;
	int blink_count = 0;
	led_blinking_t periods = {0, 1000, 0}; /* by default the led is off */

	void reinit(void)
	{
		on_ticks = periods.on_ms / portTICK_PERIOD_MS;
		off_ticks = periods.off_ms / portTICK_PERIOD_MS;
		beep_rate = periods.beep_rate;
		blink_count = 0;
	}
	reinit();

	while (1) {
		gpio_set(LED.port, LED.pin);
		if (pdPASS == xQueueReceive(led_queue, &periods, on_ticks)) {
			/* someone set a blink command, reset&continue */
			reinit();
			continue;
		}
		gpio_clear(LED.port, LED.pin);
		if (pdPASS == xQueueReceive(led_queue, &periods, off_ticks)) {
			/* someone set a blink command, reset&continue */
			reinit();
			continue;
		}
		blink_count++;
		if (blink_count == beep_rate) {
			blink_count = 0;
			if (ENABLE_BEEP_DURING_BLINK)
				ui_beep(5, 500);
		}
	}
}

static void led_init(void)
{
	rcc_periph_clock_enable(LED.rcc);
	gpio_set_mode(LED.port, GPIO_MODE_OUTPUT_2_MHZ,
		      GPIO_CNF_OUTPUT_OPENDRAIN, LED.pin);

	gpio_clear(LED.port, LED.pin);
}


static void buzzer_task(void *arg __attribute((unused)))
{
	void one_beep(int duration_ms, int tone) {
		timer_set_period(TIM1, tone);
		timer_set_oc_value(TIM1, TIM_OC2, tone / 2);
		timer_set_oc_mode(TIM1, TIM_OC2, TIM_OCM_PWM1);
		vTaskDelay(duration_ms / portTICK_PERIOD_MS);
		timer_set_oc_mode(TIM1, TIM_OC2, TIM_OCM_FORCE_LOW);
	}

	beep_t beep;
	while(1) {
		xQueueReceive(buzzer_queue, &beep, portMAX_DELAY);
		switch(beep.scale) {
		case SCALE_NO:
			one_beep(beep.duration_ms, beep.tone);
			break;
		case SCALE_UP:
			one_beep(beep.duration_ms, beep.tone);
			vTaskDelay(100 / portTICK_PERIOD_MS);
			one_beep(beep.duration_ms, beep.tone * 1.2);
			vTaskDelay(100 / portTICK_PERIOD_MS);
			one_beep(beep.duration_ms, beep.tone * 1.4);
			break;
		case SCALE_DOWN:
			one_beep(beep.duration_ms, beep.tone * 1.4);
			vTaskDelay(100 / portTICK_PERIOD_MS);
			one_beep(beep.duration_ms, beep.tone * 1.2);
			vTaskDelay(100 / portTICK_PERIOD_MS);
			one_beep(beep.duration_ms, beep.tone);
			break;
		}
	}
}

static void button_task(void *arg __attribute((unused)))
{
	const int LONG_CLICK_DELAY = 10;
	char state = 't'; // sTop, Play, FF
	char event = '0'; // 0, 'L'ong click, 'S'hort click
	int pressed_counter = 0;
	while(1) {
		vTaskDelay(100 / portTICK_PERIOD_MS);
		if (ui_antibump())
			continue;

		/****** determine which kind of event we need to handle, if any ******/
		event = '0';
		int value = gpio_get(BUTTON_PLAY.port, BUTTON_PLAY.pin);
		if (value)
			// the button is down
			pressed_counter++;

		if (pressed_counter == LONG_CLICK_DELAY) {
			// the button has been down for a while, immediatlely fire a long
			// click event
			event = 'L';
		}

		if (!value && pressed_counter > 0 && pressed_counter < LONG_CLICK_DELAY) {
			// the button is going up and it was a short press. Fire a short
			// click event
			event = 'S';
		}

		if (!value)
			pressed_counter = 0;

		/****** handle the events ******/
		if (event == 'S') {
			switch (state) {
			case 't':
				// stop ==> play
				ui_beep(30, -1);
				state = 'p';
				motor_cmd('p');
				break;
			case 'p':
				// play ==> FF
				ui_beep(100, 300);
				state = 'f';
				motor_cmd('f');
				break;
			case 'f':
				// FF ==> stop
				ui_beep(500, 500);
				state = 't';
				motor_cmd('t');
				break;
			default:
				// this should not happen, alert the user
				ui_beep(1000, -1);
				break;
			}
		}
		else if (event == 'L') {
			// toggle the direction of the motor
			int d = motor_toggle_default_direction();
			if (d > 0)
				ui_beep_scale(100, 500, SCALE_UP);
			else
				ui_beep_scale(100, 500, SCALE_DOWN);
		}
	}
}




static void buzzer_init(void)
{
	rcc_periph_clock_enable(BUZZER.rcc);
	rcc_periph_clock_enable(RCC_TIM1);

	gpio_set_mode(BUZZER.port, GPIO_MODE_OUTPUT_2_MHZ,
		      GPIO_CNF_OUTPUT_ALTFN_PUSHPULL, BUZZER.pin);

	gpio_clear(BUZZER.port, BUZZER.pin);

	timer_set_mode(TIM1, TIM_CR1_CKD_CK_INT,
		TIM_CR1_CMS_CENTER_1, TIM_CR1_DIR_DOWN);
	timer_set_repetition_counter(TIM1, 0);

	timer_continuous_mode(TIM1);

	timer_set_enabled_off_state_in_idle_mode(TIM1);
	timer_set_disabled_off_state_in_run_mode(TIM1);
	timer_disable_break(TIM1);
	timer_disable_oc_clear(TIM1, TIM_OC2);
	timer_set_oc_slow_mode(TIM1, TIM_OC2);
	timer_set_oc_polarity_high(TIM1, TIM_OC2);
	timer_set_oc_idle_state_set(TIM1, TIM_OC2);
	timer_enable_preload(TIM1);
	timer_enable_oc_preload(TIM1, TIM_OC2);
	timer_set_prescaler(TIM1, 100);
	timer_set_oc_mode(TIM1, TIM_OC2, TIM_OCM_FORCE_LOW);
	timer_set_period(TIM1, 100);
	timer_set_oc_value(TIM1, TIM_OC2, 50);
	timer_enable_counter(TIM1);
}

void ui_beep(int duration_ms, int tone)
{
	if (tone == -1)
		tone = 65;
	beep_t beep = {duration_ms, tone, SCALE_NO};
	xQueueOverwrite(buzzer_queue, &beep);
}

void ui_beep_scale(int duration_ms, int tone, beep_scale_t scale)
{
	if (tone == -1)
		tone = 65;
	beep_t beep = {duration_ms, tone, scale};
	xQueueOverwrite(buzzer_queue, &beep);
}

static void ui_antibump_init(void)
{
	rcc_periph_clock_enable(RCC_TIM2);

	timer_set_mode(TIM2, TIM_CR1_CKD_CK_INT,
		       TIM_CR1_CMS_EDGE, TIM_CR1_DIR_UP);

	timer_continuous_mode(TIM2);
	timer_set_prescaler(TIM2, 10000);
	timer_set_period(TIM2, 65535);
	timer_enable_counter(TIM2);
}

void ui_init(void)
{
	led_init();
	buzzer_init();
	if (ENABLE_BUTTONS) {
		//button_init(BUTTON_STOP);
		button_init(BUTTON_PLAY);
		//button_init(BUTTON_REWIND);
		//button_init(BUTTON_FAST_FW);
		rcc_periph_clock_enable(RCC_AFIO);	 // EXTI
		ui_antibump_init();
		//nvic_enable_irq(NVIC_EXTI4_IRQ);
		//nvic_enable_irq(NVIC_EXTI9_5_IRQ);
	}
	led_queue = xQueueCreate(1, sizeof(led_blinking_t));
	buzzer_queue = xQueueCreate(1, sizeof(beep_t));
	xTaskCreate(led_task, "led", 128, NULL, 1, NULL);
	xTaskCreate(buzzer_task, "buzzer", 128, NULL, 1, NULL);
	xTaskCreate(button_task, "button", 128, NULL, 1, NULL);
}
