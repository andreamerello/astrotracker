
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include "inv_mpu.h"
#include "inv_mpu_dmp_motion_driver.h"
#include "mpu9250.h"

/*
 * Uncomment to make the IMU sleep when acquisition is not running.
 * This has the unpleasant side effect of introducing about 10
 * seconds of distorted quaternion data
 */
//#define MPU9250_POWERSAVE


#define MPU9250_RATE 200

#define MPU9250_QUEUE_LEN 16

//#define MPU9250_USE_COMPASS

/* DMP seems to work (better) with gyro set to 2000 */
static int mpu9250_gyro_sens = 2000;
/* was 2 - 16/4/17 req. by A. Cavallo */
static int mpu9250_accel_sens = 4;
/* as per inv sense code default - 0 to bypass */
static int mpu9250_lpf = 42;

static long mpu9250_accel_bias[4];
static long mpu9250_gyro_bias[4];

static unsigned char mpu9250_sensors;

typedef struct {
	float x;
	float y;
	float z;
} VectorFloat;


typedef struct {
	float w;
	float y;
	float x;
	float z;
} Quaternion;


static void mpu9250_sensors_on()
{
#ifdef MPU9250_POWERSAVE
	if (mpu_set_sensors(mpu9250_sensors) != 0) {
		printf("MPU switch ON sensor failed\n");
	}
#endif
}

static void mpu9250_sensors_off()
{
#ifdef MPU9250_POWERSAVE
	if (mpu_set_sensors(0) != 0) {
		printf("MPU switch OFF sensor failed\n");
	}
#endif
}


int mpu9250_set_accel_sens(int sens)
{
	printf("changing ACCEL sensitivity: %d...\n", sens);
	if (mpu_set_accel_fsr(sens)!=0) {
		printf("Failed to set accel sensitivity!\n");
		return -1;
	}

	mpu9250_accel_sens = sens;
	return 0;
}

int mpu9250_set_gyro_sens(int sens)
{
	printf("changing GYRO sensitivity: %d...\n", sens);
	if (mpu_set_gyro_fsr(sens)!=0) {
		printf("Failed to set accel sensitivity!\n");
		return -1;
	}

	mpu9250_gyro_sens = sens;
	return 0;
}

int mpu9250_set_lpf(int val)
{
	printf("Setting GYRO filter bypass: %d\n", val == 0);
	if (mpu_set_lpf_by(val == 0)!=0) {
		printf("Failed to set GYRO filter bypass... \n");
		return -1;
	}

	if (val) {
		printf("Setting GYRO filter: %d... \n", val);
		if (mpu_set_lpf(val)!=0) {
			printf("Failed to set GYRO filter... \n");
			return -1;
		}
	}

	mpu9250_lpf = val;
	return 0;
}

int mpu9250_init()
{
	uint8_t devStatus; // return status after each device operation
	unsigned char fifoCount;
	int r;
	int16_t a[3];              // [x, y, z]            accel vector
	int16_t g[3];              // [x, y, z]            gyro vector
	int32_t _q[4];
	short sensors;
	unsigned long ts;
	int ret;

	if (mpu_init(NULL) != 0) {
		printf("MPU init failed!\n");
		return -1;
	}
	printf("Setting MPU sensors...\n");

#ifdef MPU9250_USE_COMPASS
	printf("Compass in use..\n");
	mpu9250_sensors = INV_XYZ_GYRO | INV_XYZ_ACCEL | INV_XYZ_COMPASS;
#else
	mpu9250_sensors = INV_XYZ_GYRO | INV_XYZ_ACCEL;
        printf("Compass DISABLED\n");
#endif
	if (mpu_set_sensors(mpu9250_sensors) != 0) {

		printf("Failed to set sensors!\n");
		return -1;
	}
	printf("Setting GYRO sensitivity: %d...\n", mpu9250_gyro_sens);
	if (mpu_set_gyro_fsr(mpu9250_gyro_sens)!=0) {
		printf("Failed to set gyro sensitivity!\n");
		return -1;
	}
	printf("Setting ACCEL sensitivity: %d...\n", mpu9250_accel_sens);
	if (mpu_set_accel_fsr(mpu9250_accel_sens)!=0) {
		printf("Failed to set accel sensitivity!\n");
		return -1;
	}

	mpu9250_set_lpf(mpu9250_lpf);

	// verify connection
	printf("Powering up MPU...\n");
	mpu_get_power_state(&devStatus);
	printf(devStatus ? "MPU6050 connection successful\n" : "MPU6050 connection failed %u\n",devStatus);

	//fifo config
	printf("Setting MPU fifo...\n");
	if (mpu_configure_fifo(INV_XYZ_GYRO|INV_XYZ_ACCEL)!=0) {
		printf("Failed to initialize MPU fifo!\n");
		return -1;
	}

	// load and configure the DMP
	printf("Loading DMP firmware...\n");
	if (dmp_load_motion_driver_firmware()!=0) {
		printf("Failed to enable DMP!\n");
		return -1;
	}
#if 0
	printf("Running self test...");

	/*
	 * This self test routine pretends the gravity vector to be perpendicular
	 * to the MPU plane. Biases are extracted from actual readings (not
	 * from factory calibrated otp). The self test result is also only
	 * meaningful when the gravity vector is perpendiculary to the decvice
	 * plane.. Probably we could skip this at all.. Unless we decide to
	 * calibrate the device when it's laying on a perfect ground.
	 * In this case note that dmp_set_accel_bias() and dmp_set_gyro_bias()
	 * only affect DMP, while probably mpu_set_accel_bias_6500_reg() and
	 * mpu_set_gyro_bias_6500_reg() do affect both DMP and 'raw' readings.
	 *
	 * result = mpu_run_self_test(gyrBias, accBias);
	 * for (i = 0; i < 3; i++) {
	 *	// The accBias values are stored in +/-8g format
	 *	accBias[i] *= 4096; // this should be 2048 for mpu9150/6050
	 *	accBias[i] = accBias[i] >> 16;
	 * }
	 * mpu_set_accel_bias_6050_reg(accBias);
	 */


	ret = mpu_run_6500_self_test(mpu9250_gyro_bias, mpu9250_accel_bias, 0);
	printf("Result: 0x%x\n", ret);

	/*
	 * Factory OTP should be already apllied to both accel/gyro 'raw'
	 * readings and DMP.. hopefully...
	 *
	 */

#endif
#if 0
	/* read factory cal. OTP */
	mpu_read_6500_accel_bias(mpu9250_accel_bias);
	printf("accel bias: %d, %d, %d\n",
			  mpu9250_accel_bias[0], mpu9250_accel_bias[1], mpu9250_accel_bias[2]);
	mpu_read_6500_gyro_bias(mpu9250_gyro_bias);
	printf("gyro bias: %d, %d, %d\n",
			  mpu9250_gyro_bias[0], mpu9250_gyro_bias[1], mpu9250_gyro_bias[2]);
#endif
	printf("Configuring DMP...\n");
	if (dmp_enable_feature(DMP_FEATURE_6X_LP_QUAT |
			       DMP_FEATURE_SEND_RAW_ACCEL |
			       DMP_FEATURE_SEND_CAL_GYRO |
			       DMP_FEATURE_GYRO_CAL) != 0) {
		printf("Failed to enable DMP features!\n");
		return -1;
	}

	printf("Setting DMP fifo rate...\n");
	if (dmp_set_fifo_rate(MPU9250_RATE)!=0) {
		printf("Failed to set dmp fifo rate!\n");
		return -1;
	}
	printf("Resetting fifo queue...\n");
	if (mpu_reset_fifo()!=0) {
		printf("Failed to reset fifo!\n");
		return -1;
	}

	printf("Activating DMP...\n");
	if (mpu_set_dmp_state(1)!=0) {
		printf("Failed to enable DMP!\n");
		return -1;
	}

	mpu9250_sensors_off();
	return 0;
}

int mpu9250_read(mpu9250_data_t *item)
{
	int ret = 0;
	unsigned char fifo_count;
	unsigned long ts;
	short sensors;

	do {
		ret = dmp_read_fifo(item->gyro, item->acc,
				    item->quat, &ts, &sensors,
				    &fifo_count);
		if (ret)
			break;
	} while(fifo_count);

#ifdef MPU9250_USE_COMPASS
	mpu_get_compass_reg(item.mpu_data.compass, NULL);
#endif

	return ret;
}

uint8_t GetGravity(VectorFloat *v, Quaternion *q) {
	v -> x = 2 * (q -> x*q -> z - q -> w*q -> y);
	v -> y = 2 * (q -> w*q -> x + q -> y*q -> z);
	v -> z = q -> w*q -> w - q -> x*q -> x - q -> y*q -> y + q -> z*q -> z;
	return 0;
}
uint8_t GetYawPitchRoll(float *data, Quaternion *q, VectorFloat *gravity) {
	// yaw: (about Z axis)
	data[0] = atan2(2*q -> x*q -> y - 2*q -> w*q -> z, 2*q -> w*q -> w + 2*q -> x*q -> x - 1);
	// pitch: (nose up/down, about Y axis)
	data[1] = atan(gravity -> x / sqrt(gravity -> y*gravity -> y + gravity -> z*gravity -> z));
	// roll: (tilt left/right, about X axis)
	data[2] = atan(gravity -> y / sqrt(gravity -> x*gravity -> x + gravity -> z*gravity -> z));
	return 0;
}

static void get_ypr(long int _q[4], float *ypr)
{
	VectorFloat gravity; // [x, y, z]            gravity vector
	Quaternion q;

	q.w = (float)_q[0]  / 16384.0f;
	q.x = (float)_q[1]  / 16384.0f;
	q.y = (float)_q[2]  / 16384.0f;
	q.z = (float)_q[3]  / 16384.0f;

	GetGravity(&gravity, &q);
	GetYawPitchRoll(ypr, &q, &gravity);
}

unsigned long long getusec()
{
	struct timespec spec;
	unsigned long long ret;

	clock_gettime(CLOCK_REALTIME, &spec);
	ret = spec.tv_sec;
	ret *= 1000;
	ret *= 1000;
	ret += spec.tv_nsec / 1000;

	return ret;
}

int main()
{
	mpu9250_data_t item;
	float ypr[3];
	int ret;
	int sample;
	unsigned long long initial_time;
	unsigned long long time;
	mpu9250_init();
	sample = 0;
	initial_time = getusec();
	while (1) {

		ret = mpu9250_read(&item);
		if (ret == 0)
			sample++;
		//printf("A %d, %d, %d\n",
		//	       item.acc[0], item.acc[1], item.acc[2]);
		//printf("G %d, %d, %d\n",
		//item.gyro[0], item.gyro[1], item.gyro[2]);
		//get_ypr(item.quat, ypr);
		//printf("YPR %f, %f, %f\n", ypr[0], ypr[1], ypr[2]);
		time = getusec();
		if ((time - initial_time) > (1000 * 1000 * 10))
			break;
	}

	printf("in 10 sec I got %d samples\n", sample);
}
