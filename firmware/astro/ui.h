#ifndef __UI__H__
#define __UI__H__

#include "tracker_config.h"

typedef enum {
	SCALE_NO = 0,
	SCALE_UP = 1,
	SCALE_DOWN = 2,
} beep_scale_t;

void ui_init(void);
void set_led_blink(int on_ms, int off_ms, int beep_rate);
void set_led_on(void);
void set_led_off(void);
void ui_beep(int duration_ms, int tone);
void ui_beep_scale(int duration_ms, int tone, beep_scale_t scale);
#endif
