#ifndef TRACKER_CONFIG_H
#define TRACKER_CONFIG_H

#include <stdbool.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include "bluepill.h"

// we support two kind of trackers: BARN_DOOR (also know as "v1") and MINITRACK
// (also know as "v2")

// uncomment only one of the two lines
//#define BARN_DOOR
#define MINITRACK

#if defined(BARN_DOOR) && defined(MINITRACK)
#  error "You cannot define both BARN_DOOR and MINITRACK. See tracker_config.h"
#endif

#if !defined(BARN_DOOR) && !defined(MINITRACK)
#  error "You MUST define either BARN_DOOR or MINITRACK. See tracker_config.h"
#endif

#if defined(BARN_DOOR)
/***** GEOMETRY *****/
static const long STEPS_FOR_10_DEGREES = 19955UL;
static const long STEPS_FOR_360_DEGREES = STEPS_FOR_TEN_DEGREES * 36;
static const int MOTOR_MAX_POSITION = (int)(STEPS_FOR_10_DEGREES * 1.5);
static const int HOME_QUIT_STEPS =  (int)(STEPS_FOR_10_DEGREES / 10);

/***** ELECTRONIC *****/
// external led attached to PC13
static const bool LED_IS_INVERTED = false;
static const pin_t LED = PIN_C13;
static const pin_t BUZZER = PIN_A9;
static const bool ENABLE_BUTTONS = true;

// "motor wires" refers to the wires attached to the motors: in the datasheet
// they are often labeled as A1, A2, B1, B2 or A, A/, B, B/
//
// motor wires:         A1      A2      B1      B2
#define MOTOR_PINS {PIN_A1, PIN_A3, PIN_A0, PIN_A2}
#define MOTOR_BIPOLAR

#elif defined(MINITRACK)
/***** GEOMETRY *****/
// 512 are the steps for a full rotation of the motor
//  27 is the reduction of the gearbox
//  41 the number of teeth of the big gear after the worm gear
static const long STEPS_FOR_360_DEGREES = 512 * 27 * 41;


/***** ELECTRONIC *****/
static const bool LED_IS_INVERTED = true;
static const pin_t LED = PIN_C13;
static const pin_t BUZZER = PIN_A9;
static const bool ENABLE_BUTTONS = false;

// motor wires:         A1      A2      B1      B2
#define MOTOR_PINS {PIN_A0, PIN_A3, PIN_A5, PIN_A6}
#define MOTOR_UNIPOLAR

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
