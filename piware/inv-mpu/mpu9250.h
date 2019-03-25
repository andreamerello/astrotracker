#ifndef __MPU9250_H__
#define __MPU9250_H__

#include <stdint.h>

typedef struct {
	long int quat[4];
	int16_t acc[3];
	int16_t gyro[3];
	/* must be the last one */
	int16_t compass[3];
} mpu9250_data_t;

extern int mpu9250_init();
extern int mpu9250_read(mpu9250_data_t *);
extern int mpu9250_set_gyro_sens(int sens);
extern int mpu9250_set_accel_sens(int sens);
extern int mpu9250_set_lpf(int val);

#endif
