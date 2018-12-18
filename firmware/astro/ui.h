#ifndef __UI__H__
#define __UI__H__

//#define DEBUG
#undef DEBUG

#ifdef DEBUG
#define my_printf std_printf
#else
#define my_printf(...) ;
#endif

void ui_init(void);
void set_led_blink(int on_ms, int off_ms);
void set_led_on(void);
void set_led_off(void);

#endif
