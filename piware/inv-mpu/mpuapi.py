from __future__ import print_function
from collections import namedtuple
from _mpuapi import ffi, lib
import math

MpuData = namedtuple('MpuData', ['yaw', 'pitch', 'roll', 'accel', 'gyro'])
Accel = namedtuple('Accel', ['x', 'y', 'z'])
Gyro = namedtuple('Gyro', ['x', 'y', 'z'])

class MpuException(Exception):
    pass

class MpuApi(object):
    # accel sensitivity has been tested with 2 and 4 and DMP seems to work...
    def __init__(self, accel_sensitivity=2, sample_rate=200, verbose=True):
        self.verbose = verbose
        self.quat_data = ffi.new("long[4]")
        self.gyro_data = ffi.new("short[3]")
        self.accel_data = ffi.new("short[3]")
        self.sensors = ffi.new("short[1]")
        self.fifo_count = ffi.new("unsigned char[1]")
        self.ypr = ffi.new("float[3]")

        gyro_sensitivity = 2000

        if lib.mpu_init(ffi.NULL) != 0:
	    raise MpuException("MPU init failed!")

	sensors = lib.INV_XYZ_GYRO | lib.INV_XYZ_ACCEL
	if lib.mpu_set_sensors(sensors) != 0:
	    raise MpuException("Failed to set sensors!")

	self.log("Setting GYRO sensitivity: %d..." % gyro_sensitivity)
	if lib.mpu_set_gyro_fsr(gyro_sensitivity) != 0:
	    raise MpuException("Failed to set gyro sensitivity!")

	self.log("Setting ACCEL sensitivity: %d..." % accel_sensitivity)
	if lib.mpu_set_accel_fsr(accel_sensitivity) != 0:
	    raise MpuException("Failed to set accel sensitivity!")

	if lib.mpu_configure_fifo(sensors) != 0:
	    raise MpuException("Failed to initialize MPU fifo!")

	if lib.dmp_load_motion_driver_firmware() != 0:
	    raise MpuException("Failed to enable DMP!")

	if lib.dmp_enable_feature(lib.DMP_FEATURE_6X_LP_QUAT |
			          lib.DMP_FEATURE_SEND_RAW_ACCEL |
			          lib.DMP_FEATURE_SEND_CAL_GYRO |
			          lib.DMP_FEATURE_GYRO_CAL) != 0:
		raise MpuException("Failed to enable DMP features!")

	if lib.dmp_set_fifo_rate(sample_rate) != 0:
	    raise MpuException("Failed to set dmp fifo rate!")
        self.log("Setting IMU sample rate to {:d}Hz".format(sample_rate))
	if lib.mpu_reset_fifo() != 0:
	    raise MpuException("Failed to reset fifo!")

	if lib.mpu_set_dmp_state(1) != 0:
	    raise MpuException("Failed to enable DMP!")

    def read_one_item(self):
        while True:
            ret = lib.dmp_read_fifo(self.gyro_data, self.accel_data,
				    self.quat_data, ffi.NULL, self.sensors,
				    self.fifo_count)
            if ret != 0:
                return None

            if self.fifo_count[0] == 0:
                break

        lib.get_ypr(self.quat_data, self.ypr)
        y, p, r = map(math.degrees, self.ypr)
        data = MpuData(y, p, r,
                       Accel(self.accel_data[0], self.accel_data[1], self.accel_data[2]),
                       Gyro(self.gyro_data[0], self.gyro_data[1], self.gyro_data[2]))

        return data

    def __iter__(self):
        while True:
            yield self.read_one_item()

    def log(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)


if __name__ == '__main__':
    import time
    mpu = MpuApi(sample_rate=100)
    i = 0
    for data in mpu:
        if data is None:
            continue
        if True: #i == 1000:
            print("pitch{:7.2f}, roll{:7.2f}, yaw{:7.2f}".format(data.pitch, data.roll, data.yaw))
            i = 0
        i += 1
