#ifndef __RTC_H__
#define __RTC_H__
#include <stdint.h>

void rtc_init(void);
void rtc_reset(void);
uint32_t rtc_get_ticks(void);

#endif
