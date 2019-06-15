#!/usr/bin/python

from cffi import FFI
ffibuilder = FFI()


ffibuilder.set_source("_mpuapi",
                      """
                      #include "inv_mpu.h"
                      #include "inv_mpu_dmp_motion_driver.h"
                      #include "quat_ypr.h"
                      """,
                      libraries=['m'],
                      sources=['inv_mpu.c', 'inv_mpu_dmp_motion_driver.c', 'quat_ypr.c'],
                      include_dirs=['.'],
                      )

ffibuilder.cdef("""
	#define INV_X_GYRO      ...
	#define INV_Y_GYRO      ...
	#define INV_Z_GYRO      ...
	#define INV_XYZ_GYRO    ...
	#define INV_XYZ_ACCEL   ...
	#define INV_XYZ_COMPASS ...

        #define DMP_FEATURE_6X_LP_QUAT ...
	#define DMP_FEATURE_SEND_RAW_ACCEL ...
	#define DMP_FEATURE_SEND_CAL_GYRO ...
	#define DMP_FEATURE_GYRO_CAL ...

	struct int_param_s;
	int dmp_load_motion_driver_firmware(void);
	int mpu_set_dmp_state(unsigned char enable);
	int mpu_get_dmp_state(unsigned char *enabled);

	int mpu_get_gyro_fsr(unsigned short *fsr);
	int mpu_set_gyro_fsr(unsigned short fsr);
	int mpu_get_fifo_config(unsigned char *sensors);
	int mpu_configure_fifo(unsigned char sensors);
	int mpu_read_fifo(short *gyro, short *accel, unsigned long *timestamp, unsigned char *sensors, unsigned char *more);
	int mpu_read_fifo_stream(unsigned short length, unsigned char *data, unsigned char *more);
	int mpu_reset_fifo(void);

	int mpu_get_accel_fsr(unsigned char *fsr);
	int mpu_set_accel_fsr(unsigned char fsr);
	int mpu_set_sensors(unsigned char sensors);
	int mpu_init(struct int_param_s *int_param);
	int dmp_set_fifo_rate(unsigned short rate);
	int dmp_get_fifo_rate(unsigned short *rate);
	int dmp_enable_feature(unsigned short mask);
	int dmp_read_fifo(short *gyro, short *accel, long *quat,
		unsigned long *timestamp, short *sensors, unsigned char *more);
	void get_ypr(long int _q[4], float *ypr);
""")


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
