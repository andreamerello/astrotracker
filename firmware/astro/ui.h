#ifndef __UI__H__
#define __UI__H__

#ifndef __maybe_unused
# define __maybe_unused		__attribute__((unused))
#endif

//#define DEBUG
#undef DEBUG

#define ENABLE_KEYBOARD_COMMANDS


#ifdef DEBUG
#define my_printf std_printf
#else
#define my_printf(...) ;
#undef ENABLE_KEYBOARD_COMMANDS
#endif

void ui_init(void);
void set_led_blink(int on_ms, int off_ms, int beep_rate);
void set_led_on(void);
void set_led_off(void);
void ui_beep(int duration_ms, int tone);
#endif
