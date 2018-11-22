#include <stdint.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include <libopencm3/stm32/exti.h>
#include <libopencm3/cm3/nvic.h>

#include "FreeRTOS.h"
#include "ui.h"
#include "motor.h"
#include "task.h"

typedef struct {
	uint32_t port;
	uint32_t pin;
	uint32_t rcc;
    uint32_t exti;
} button_t;

/* these GPIO have internal pull-downs */
static button_t BUTTON_STOP    = { GPIOA, GPIO4, RCC_GPIOA, EXTI4 };
static button_t BUTTON_PLAY    = { GPIOA, GPIO5, RCC_GPIOA, EXTI5 };
static button_t BUTTON_REWIND  = { GPIOA, GPIO6, RCC_GPIOA, EXTI6 };
static button_t BUTTON_FAST_FW = { GPIOA, GPIO8, RCC_GPIOA, EXTI8 };

static void button_init(button_t btn)
{
    rcc_periph_clock_enable(btn.rcc);
    gpio_set_mode(btn.port, GPIO_MODE_INPUT, GPIO_CNF_INPUT_PULL_UPDOWN, btn.pin);
	exti_select_source(btn.exti, btn.port);
	exti_set_trigger(btn.exti, EXTI_TRIGGER_FALLING);
	exti_enable_request(btn.exti);
}

void exti4_isr(void)
{
    if (exti_get_flag_status(BUTTON_STOP.exti)) {
        motor_cmd_from_isr('t');
        exti_reset_request(BUTTON_STOP.exti);
    }
}

void exti9_5_isr(void)
{
    if (exti_get_flag_status(BUTTON_PLAY.exti)) {
        motor_cmd_from_isr('s');
        exti_reset_request(BUTTON_PLAY.exti);
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

/* WARNING: you need to have phisical pull-ups to make this working */
void ui_init(void)
{
    button_init(BUTTON_STOP);
    button_init(BUTTON_PLAY);
    button_init(BUTTON_REWIND);
    button_init(BUTTON_FAST_FW);
	rcc_periph_clock_enable(RCC_AFIO);	 // EXTI
    nvic_enable_irq(NVIC_EXTI4_IRQ);
    nvic_enable_irq(NVIC_EXTI9_5_IRQ);
}
