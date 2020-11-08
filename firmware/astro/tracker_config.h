#ifndef TRACKER_CONFIG_H
#define TRACKER_CONFIG_H

// we support two kind of trackers: BARN_DOOR (also know as "v1") and MINITRACK
// (also know as "v2")

// uncooment only one of the two lines
#define BARN_DOOR
//#define MINITRACK

#if defined(BARN_DOOR) && defined(MINITRACK)
#  error "You cannot define both BARN_DOOR and MINITRACK. See tracker_config.h"
#endif

#if !defined(BARN_DOOR) && !defined(MINITRACK)
#  error "You MUST define either BARN_DOOR or MINITRACK. See tracker_config.h"
#endif


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
