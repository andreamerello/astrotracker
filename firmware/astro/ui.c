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

static button_t BUTTON_STOP   = { GPIOB, GPIO12, RCC_GPIOB, EXTI12 };
static button_t BUTTON_PLAY  = { GPIOB, GPIO13, RCC_GPIOB, EXTI13 };
static button_t BUTTON_REWIND = { GPIOB, GPIO14, RCC_GPIOB, EXTI14 };

static void button_init(button_t btn)
{
    rcc_periph_clock_enable(btn.rcc);
    gpio_set_mode(btn.port, GPIO_MODE_INPUT, GPIO_CNF_INPUT_PULL_UPDOWN, btn.pin);
	exti_select_source(btn.exti, btn.port);
	exti_set_trigger(btn.exti, EXTI_TRIGGER_FALLING);
	exti_enable_request(btn.exti);
}

void exti15_10_isr()
{
    if (exti_get_flag_status(BUTTON_STOP.exti)) {
        motor_cmd_from_isr('t');
        exti_reset_request(BUTTON_STOP.exti);
    }
    if (exti_get_flag_status(BUTTON_PLAY.exti)) {
        motor_cmd_from_isr('s');
        exti_reset_request(BUTTON_PLAY.exti);
    }
    if (exti_get_flag_status(BUTTON_REWIND.exti)) {
        motor_cmd_from_isr('r');
        exti_reset_request(BUTTON_REWIND.exti);
    }
}

/* WARNING: you need to have phisical pull-ups to make this working */
void ui_init(void)
{
    button_init(BUTTON_STOP);
    button_init(BUTTON_PLAY);
    button_init(BUTTON_REWIND);
	rcc_periph_clock_enable(RCC_AFIO);	 // EXTI
    nvic_enable_irq(NVIC_EXTI15_10_IRQ); // PC14 <- /INT
}
