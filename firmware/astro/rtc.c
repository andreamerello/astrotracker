#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/rtc.h>

#include "rtc.h"

void rtc_init(void)
{
	rcc_enable_rtc_clock();
	rtc_interrupt_disable(RTC_SEC);
	rtc_interrupt_disable(RTC_ALR);
	rtc_interrupt_disable(RTC_OW);

	/* use 32KHz xtal for RTC */
	rtc_awake_from_off(RCC_LSE);
	rtc_set_prescale_val(0);
	rtc_set_counter_val(0x0);

	/*
	nvic_enable_irq(NVIC_RTC_IRQ);

	cm_disable_interrupts();
	rtc_clear_flag(RTC_SEC);
	rtc_clear_flag(RTC_ALR);
	rtc_clear_flag(RTC_OW);
	rtc_interrupt_enable(RTC_SEC);
	rtc_interrupt_enable(RTC_ALR);
	rtc_interrupt_enable(RTC_OW);
	cm_enable_interrupts();
	*/
}

void rtc_reset(void)
{
	rtc_set_counter_val(0x0);
}

uint32_t rtc_get_ticks(void)
{
	return rtc_get_counter_val();
}
