#ifndef TRACKER_CONFIG_H
#define TRACKER_CONFIG_H

#include <stdbool.h>
#include <libopencm3/stm32/rcc.h>
#include <libopencm3/stm32/gpio.h>
#include "bluepill.h"


//#define DEBUG
#undef DEBUG



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
static const int DEFAULT_DIRECTION = 1;
static const long _STEPS_FOR_10_DEGREES = 19955UL;
static const long STEPS_FOR_360_DEGREES = _STEPS_FOR_TEN_DEGREES * 36;
static const int MOTOR_MAX_POSITION = (int)(_STEPS_FOR_10_DEGREES * 1.5);
static const int HOME_QUIT_STEPS =  (int)(_STEPS_FOR_10_DEGREES / 10);

/***** ELECTRONIC *****/
// external led attached to PC13
static const bool LED_IS_INVERTED = false;
static const pin_t LED = PIN_C13;
static const pin_t BUZZER = PIN_A9;
static const bool ENABLE_BUTTONS = true;

/* this GPIO has an internal pull-up */
#define HOMING_PIN GPIO15
#define HOMING_PORT GPIOA
#define HOMING_RCC RCC_GPIOA


// "motor wires" refers to the wires attached to the motors: in the datasheet
// they are often labeled as A1, A2, B1, B2 or A, A/, B, B/
//
// motor wires:         A1      A2      B1      B2
#define MOTOR_PINS {PIN_A1, PIN_A3, PIN_A0, PIN_A2}
#define MOTOR_BIPOLAR

/* FF speed: number of ticks to wait between a step and the next

   by experimenting we found out that 130 is the magic number for the maximum
   speed the motor can handle. However in at least one occasion, it didn't
   work when battery powered (maybe because there was not enough voltage?) So
   we consevatively run a bit slower
*/
static const int FF_TICKS_PER_STEP = 200;


#elif defined(MINITRACK)
/***** GEOMETRY *****/
//   8.89 is the radius of the circular M4 threaded rod (in cm)
//   0.05 is the pitch of the M4 threaded rod (in cm)
//   2*pi*radius / pitch is the number of teeth for 360 degrees
// 512 are the steps for a full rotation of the motor
//   8 is the number of rows in motor.c:magic_table (it's hardcoded, I know :( )
static const long STEPS_FOR_360_DEGREES = (8.89*2*3.14)/0.5 * 512 * 8;
static const int DEFAULT_DIRECTION = -1;

/***** ELECTRONIC *****/
static const bool LED_IS_INVERTED = true;
static const pin_t LED = PIN_C13;
static const pin_t BUZZER = PIN_A9;
static const bool ENABLE_BUTTONS = true; // XXX

// motor wires:         A1      A2      B1      B2
#define MOTOR_PINS {PIN_A0, PIN_A3, PIN_A5, PIN_A6}
#define MOTOR_UNIPOLAR

static const int FF_TICKS_PER_STEP = 30; // found experimentally

#endif /* BARN_DOOR or MINITRACK */



#define ENABLE_KEYBOARD_COMMANDS
#define ENABLE_DEBUG_MOTOR_COMMANDS

// if it's true, the buzzer will beep during PLAY and FF
static const int ENABLE_BEEP_DURING_BLINK = 0;


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
