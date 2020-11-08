#ifndef TRACKER_CONFIG_H
#define TRACKER_CONFIG_H

#include <stdbool.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>

// we support two kind of trackers: BARN_DOOR (also know as "v1") and MINITRACK
// (also know as "v2")

// uncomment only one of the two lines
#define BARN_DOOR
//#define MINITRACK

#if defined(BARN_DOOR) && defined(MINITRACK)
#  error "You cannot define both BARN_DOOR and MINITRACK. See tracker_config.h"
#endif

#if !defined(BARN_DOOR) && !defined(MINITRACK)
#  error "You MUST define either BARN_DOOR or MINITRACK. See tracker_config.h"
#endif



#if defined(BARN_DOOR)
// external led attached to PC13
static const bool LED_IS_INVERTED = false;
static const int LED_PORT = GPIOC;
static const int LED_PIN = GPIO13;
static const int LED_RCC = RCC_GPIOC;

#elif defined(MINITRACK)
static const bool LED_IS_INVERTED = true;
static const int LED_PORT = GPIOC;
static const int LED_PIN = GPIO13;
static const int LED_RCC = RCC_GPIOC;

#endif /* BARN_DOOR or MINITRACK */



#define DEBUG
//#undef DEBUG

#define ENABLE_KEYBOARD_COMMANDS
#define ENABLE_DEBUG_MOTOR_COMMANDS


#ifdef DEBUG
#  define my_printf std_printf
#else
#  define my_printf(...) ;
#  undef ENABLE_KEYBOARD_COMMANDS
#  undef ENABLE_DEBUG_MOTOR_COMMANDS
#endif

#ifndef __maybe_unused
# define __maybe_unused		__attribute__((unused))
#endif


#endif
