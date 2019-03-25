#include <stdint.h>
#include <math.h>

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

static uint8_t GetGravity(VectorFloat *v, Quaternion *q) {
	v -> x = 2 * (q -> x*q -> z - q -> w*q -> y);
	v -> y = 2 * (q -> w*q -> x + q -> y*q -> z);
	v -> z = q -> w*q -> w - q -> x*q -> x - q -> y*q -> y + q -> z*q -> z;
	return 0;
}
static uint8_t GetYawPitchRoll(float *data, Quaternion *q, VectorFloat *gravity) {
	// yaw: (about Z axis)
	data[0] = atan2(2*q -> x*q -> y - 2*q -> w*q -> z, 2*q -> w*q -> w + 2*q -> x*q -> x - 1);
	// pitch: (nose up/down, about Y axis)
	data[1] = atan(gravity -> x / sqrt(gravity -> y*gravity -> y + gravity -> z*gravity -> z));
	// roll: (tilt left/right, about X axis)
	data[2] = atan(gravity -> y / sqrt(gravity -> x*gravity -> x + gravity -> z*gravity -> z));
	return 0;
}

void get_ypr(long int _q[4], float *ypr)
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
