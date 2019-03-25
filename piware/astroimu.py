
### TODO: filtro fa cagare, usare i valori accel per trovare angoli con le magie su github.
### Controllare accell totale e fare qualcosa di sensato


import sys
sys.path.append("inv-mpu")

import time
import math
from mpuapi import MpuApi, Accel


class Lowpass(object):
    def __init__(self, tau):
        self.tau = tau
        self.output = None

    def __call__(self, val):
        if self.output is None:
            self.output = val
        self.output = (self.tau * self.output + val) / (self.tau + 1)
        return self.output

def main():
    fs = 100   # freq sample
    tau = 400.0 #
    order = 1
    low_pass = Accel(
        x = Lowpass(tau),
        y = Lowpass(tau),
        z = Lowpass(tau),
    )
    mpu = MpuApi(sample_rate=fs)
    for data in mpu:
        if data is None:
            continue
        a = Accel(
            low_pass.x(data.accel.x),
            low_pass.y(data.accel.y),
            low_pass.z(data.accel.z)
        )
        total_acc = math.hypot(math.hypot(a.x, a.y), a.z)
        print("tot {:7.2f}, x{:7.2f}, y{:7.2f}, z{:7.2f}".format(
            total_acc, a.x, a.y, a.z))


if __name__ == '__main__':
    main()
