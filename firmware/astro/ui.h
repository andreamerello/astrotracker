#ifndef __UI__H__
#define __UI__H__

#include "tracker_config.h"

void ui_init(void);
void set_led_blink(int on_ms, int off_ms, int beep_rate);
void set_led_on(void);
void set_led_off(void);
void ui_beep(int duration_ms, int tone);
#endif
