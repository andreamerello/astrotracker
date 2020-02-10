import math
import cv2
import numpy as np
from stars import STARS, SkyPoint
import cartesian
from cartesian import YELLOW, RED
from cvextra import CvTrackbar

PI = np.pi
NORTH_POLE = SkyPoint(0, PI/2)

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
    rho = dec / (PI/2) # scale to a total 90° range (-45° to +45°)
    phi = ra
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

## class Camera:

##     def __init__(self, ra, dec):
##         self.ra = ra
##         self.dec = dec
##         self.horiz_angle = np.deg2rad(4.24)   # angle of view of APS-C @ 300mm
##         self.vert_angle = np.deg2rad(2.83)

##     def draw(self, sky):
##         w = sky.width / sky.dec_width * self.horiz_angle / 2
##         h = sky.width / sky.dec_width * self.vert_angle  / 2
##         x, y = sky.radec2xy(self.ra, self.dec)
##         p1 = int(x-w/2), int(y-h/2)
##         p2 = int(x+w/2), int(y+h/2)
##         cv2.rectangle(sky.img, p1, p2, [0, 255, 0])


def find_star(n):
    for s in STARS:
        if s.hipparcos == n:
            return s
    raise KeyError(n)

MIZAR = find_star(65378)



class Simulation:

    def __init__(self):
        #cv2.moveWindow('sky', 5280, 0) # TEMP, Move to my 3rd screen
        self.sky = Sky(1000, 1.0)
        self.sky_win = cartesian.Window('sky', self.sky, self.draw_sky)
        self.t = CvTrackbar('t', 'sky', 0, 60*60*24, self.update)
        ## self.camera = Camera(MIZAR.ra, MIZAR.dec)

    def update(self, value):
        self.sky_win.show()

    def draw_sky(self):
        t = self.t.value
        self.sky.clear()
        for star in STARS:
            self.sky.draw_star(star, t)

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
