#ifndef __MOTOR__H__
#define __MOTOR__H__

#include "tracker_config.h"

void motor_init(void);
void motor_cmd(char c);
void motor_cmd_from_isr(char c);

#endif
