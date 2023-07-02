SIDEREAL_DAY = 86164 # 23h 56m 4s

def compute(tracker):
    usteps_per_revolution = (tracker.MOTOR_STEPS *
                             tracker.GEARBOX_RATIO *
                             tracker.MICROSTEPS)
    usteps_per_sec = usteps_per_revolution / SIDEREAL_DAY
    delay = 1 / usteps_per_sec

    print(f'=== {tracker.name} ===')
    print(f'Motor steps per 360°: {tracker.MOTOR_STEPS}')
    print(f'Microsteps per step:  {tracker.MICROSTEPS}')
    print(f'Total gearbox ratio:  {tracker.GEARBOX_RATIO:8.4f}')
    print(f'Microsteps/sec:       {usteps_per_sec:9.4f}')
    print(f'Delay between usteps: {delay*1000:9.4f} ms')
    # to make a microstep, we need two halves: half time to put the pin HIGH,
    # half time to put it LOW
    print(f'Delay between pulses: {delay/2*1000:9.4f} ms')
    print()


class OGTacker:
    name = 'OG Tracker'
    MOTOR_STEPS = 400   # steps for a full 360° rotation
    MICROSTEPS = 16     # how many "pulses" we need to make to achieve 1 step
    GEARBOX_RATIO = 48/16 * 48/16 * 180/16


class GoldTracker:
    name = 'Gold Tracker'
    MOTOR_STEPS = 400   # steps for a full 360° rotation
    GEARBOX_RATIO = 188 * 200/17
    MICROSTEPS = 2


compute(OGTacker)
compute(GoldTracker)
