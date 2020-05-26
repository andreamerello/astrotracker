import math
import cv2
import numpy as np
from stars import STARS, SkyPoint
import cartesian
from cartesian import YELLOW, RED, GREEN, MAGENTA
from cvextra import CvTrackbar

PI = np.pi
NORTH_POLE = SkyPoint(0, PI/2)
UNIT_PER_DEC = 1.0 / (PI/2) # -45°..+45° ==> -1..+1

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y

def radec2cart(p):
    """
    Convert from RA/DEC coordinates to cartesian.

    The North Pole is at (0, 0). Results are in the range -1.0, +1.0 for the
    range from -45° to +45°
    """
    ra = p.ra
    dec = p.dec
    # center on the north pole
    if dec < 0:
        dec += PI/2
    else:
        dec -= PI/2
    rho = dec * UNIT_PER_DEC
    phi = -ra
    return pol2cart(rho, phi)

def _rotate(point, radians, origin=(0, 0)):
    """
    Rotate a point around a given point.
    """
    x, y = point
    ox, oy = origin
    qx = ox + math.cos(radians) * (x - ox) + math.sin(radians) * (y - oy)
    qy = oy + -math.sin(radians) * (x - ox) + math.cos(radians) * (y - oy)
    return qx, qy

def rotate(point, origin, angular_speed, t):
    """
    Rotate a point at a given time, accordig to its angular_speed
    """
    radians = angular_speed * t
    return _rotate(point, radians, origin)



class Sky(cartesian.Image):
    """
    A cartesian plane in which we can draw stars (whose coordinates are
    expressed in RA/DEC)
    """

    # this is not completely accurate, but it's not important for the purposes
    # of this simulation
    ANGULAR_SPEED = (np.pi*2)/(60*60*24) # 360 deg / 24h, radians/s

    def clear(self):
        super(Sky, self).clear()
        self.set(radec2cart(NORTH_POLE), color=RED)

    def draw_star(self, star, t):
        # draw a star in the sky at the time t
        p0 = radec2cart(star) # position at t==0
        pt = rotate(p0, (0, 0), self.ANGULAR_SPEED, t)
        self.set(pt, YELLOW)

class Camera:

    def __init__(self, p0, tracker_p, tracker_speed):
        """
        p0: center of the camera at t==0, expressed in RA/DEC
        tracker_p: rotation center of the tracker, in RA/DEC
        tracker_speed: angular speed of the tracker, in radians/sec
        """
        self.p0 = p0
        self.tracker_p = tracker_p
        self.tracker_speed = tracker_speed
        # angle of view of APS-C @ 300mm
        self.width = np.deg2rad(4.24) * UNIT_PER_DEC
        self.height = np.deg2rad(2.83) * UNIT_PER_DEC

        #...
        # an image for the full sensor would be 3984x2656, with
        # unit_width==sky.unit_width/self.width (or self.height, since cartesian.Image
        # assumes a square)
        #self.img = cartesian.Image(...)



    def draw(self, sky, t):
        W = self.width
        H = self.height
        # compute the corners of the camera at t0
        x0, y0 = radec2cart(self.p0)
        a0 = (x0-W/2, y0-H/2)
        b0 = (x0-W/2, y0+H/2)
        c0 = (x0+W/2, y0+H/2)
        d0 = (x0+W/2, y0-H/2)
        #
        # rotate the corners at the given t
        tracker_p = radec2cart(self.tracker_p)
        at = rotate(a0, tracker_p, self.tracker_speed, t)
        bt = rotate(b0, tracker_p, self.tracker_speed, t)
        ct = rotate(c0, tracker_p, self.tracker_speed, t)
        dt = rotate(d0, tracker_p, self.tracker_speed, t)
        #
        # draw the rectangle
        sky.line(at, bt, GREEN)
        sky.line(bt, ct, GREEN)
        sky.line(ct, dt, GREEN)
        sky.line(dt, at, GREEN)
        sky.set(tracker_p, MAGENTA)


def find_star(n):
    for s in STARS:
        if s.hipparcos == n:
            return s
    raise KeyError(n)

MIZAR = find_star(65378)



class Simulation:

    def __init__(self):
        #cv2.moveWindow('sky', 5280, 0) # TEMP, Move to my 3rd screen
        self.sky = Sky(1000, 1.5)
        self.sky_win = cartesian.Window('sky', self.sky, self.draw_sky)
        self.t = CvTrackbar('t', 'sky', 0, 60*60*24, self.update)
        self.camera = Camera(MIZAR, SkyPoint(0, PI/3), self.sky.ANGULAR_SPEED)

    def update(self, value):
        self.sky_win.show()

    def draw_sky(self):
        t = self.t.value
        self.sky.clear()
        for star in STARS:
            self.sky.draw_star(star, t)
        self.camera.draw(self.sky, t)

    def is_window_visible(self):
        # I don't know why, but WND_PROP_VISIBLE does not seem to work :(
        return cv2.getWindowProperty("sky", cv2.WND_PROP_AUTOSIZE) == 1

    def run(self):
        fps = 4.0
        ms_delay = int(1000/fps) # milliseconds per frame
        self.sky_win.show()
        while self.is_window_visible():
            ch = chr(cv2.waitKey(ms_delay) & 0xFF)
            if ch == 'q':
                break


def main():
    sim = Simulation()
    sim.run()

if __name__ == '__main__':
    main()
