import math
import cv2
import numpy as np
from stars import STARS, SkyPoint

"""
Naming convention:

ra, dec: celestial coordinates
x, y:    cartesian coordinates (from -1.0 to +1.0)
i, j:    image coordinates (i.e., indexes into the numpy array)
"""

PI = np.pi
NORTH_POLE = SkyPoint(0, PI/2)

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y

def radec2cart(ra, dec):
    """
    Convert from RA/DEC coordinates to cartesian.

    The North Pole is at (0, 0). Results are in the range -1.0, +1.0 for the
    range from -45° to +45°
    """
    # center on the north pole
    if dec < 0:
        dec += PI/2
    else:
        dec -= PI/2
    rho = dec / (PI/2) # scale to a total 90° range (-45° to +45°)
    phi = ra
    return pol2cart(rho, phi)


class ViewPort:

    def __init__(self, name, width):
        self.name = name
        self.width = width
        self.time = 0
        #self.angular_speed = PI*2 / (24*60*60) # 360 deg in 24hrs
        self.img = np.zeros(shape=[self.width, self.width, 3], dtype=np.uint8)
        self.clear()

    def clear(self):
        self.img.fill(0)

    def set(self, p, color):
        x, y = radec2cart(p.ra, p.dec)
        i, j = self.cart2index(x, y)
        self.set_pixel(i, j, color)

    def cart2index(self, x, y):
        # x, y are in range -1..1. Tranform to image coordinates
        # note that "i" corresponds to the Y axis, "j" to the X axis
        j = (x+1) * (self.width/2)
        i = (y+1) * (self.width/2)
        return int(i), int(j)

    def radec2index(self, p):
        x, y = radec2cart(p.ra, p.dec)
        return self.cart2index(x, y)

    def set_pixel(self, i, j, color):
        # if we pass a float it's very likely that we are passing a (x, y)
        # instead of a (i, j)
        assert type(i) == type(j) == int
        if 0 <= i < self.width and 0 <= j < self.width:
            self.img[i, j] = color


class Sky:

    GRID_COLOR = (40, 40, 40)

    def __init__(self):
        self.sky_viewport = ViewPort('sky', 1000)

    def show(self):
        cv2.imshow('sky', self.sky_viewport.img)

    def clear(self):
        self.sky_viewport.clear()
        self.draw_grid()

    def draw_star(self, s):
        self.sky_viewport.set(s, color=[0, 255, 255])

    def draw_grid(self):
        # draw additional lines in the sky_viewport, not affecting other viewports
        if self.GRID_COLOR:
            for hr in range(24):
                self.draw_meridian(np.deg2rad(15*hr))
            for dec in range(0, 90, 10):
                self.draw_parallel(np.deg2rad(dec))
            self.draw_parallel(np.deg2rad(85))
        self.sky_viewport.set(NORTH_POLE, color=[0, 0, 255])

    def draw_parallel(self, dec):
        i, j = self.sky_viewport.radec2index(SkyPoint(ra=0, dec=NORTH_POLE.dec-dec))
        radius = j
        center = self.sky_viewport.radec2index(NORTH_POLE)
        cv2.circle(self.sky_viewport.img, center, radius, self.GRID_COLOR)

    def draw_meridian(self, ra):
        p1 = self.sky_viewport.radec2index(NORTH_POLE)
        p2 = self.sky_viewport.radec2index(SkyPoint(ra, dec=0))
        cv2.line(self.sky_viewport.img, p1, p2, self.GRID_COLOR)



class CvTrackbar:

    def __init__(self, name, win, min, max, callback, default=None):
        self.name = name
        self.win = win
        cv2.createTrackbar(name, win, min, max, callback)
        if default is not None:
            self.value = default

    @property
    def value(self):
        return cv2.getTrackbarPos(self.name, self.win)

    @value.setter
    def value(self, v):
        cv2.setTrackbarPos(self.name, self.win, v)


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
        cv2.namedWindow("sky")
        cv2.moveWindow('sky', 5280, 0) # TEMP, Move to my 3rd screen

        self.ready = False
        self.zoom = CvTrackbar('zoom', 'sky', 1, 10, self.update)
        self.time = CvTrackbar('time', 'sky', 0, 60*60*24, self.update)
        self.sky = Sky()
        ## self.camera = Camera(MIZAR.ra, MIZAR.dec)
        self.ready = True
        self.GRID = True

    def update(self, value=None):
        if not self.ready:
            return
        if self.zoom.value == 0:
            self.zoom.value = 1
            return
        #self.sky.dec_width = PI/2 / self.zoom.value
        #self.sky.time = self.time.value

        self.sky.clear()
        for star in STARS:
            self.sky.draw_star(star)

        #self.camera.draw(self.sky)
        self.sky.show()

    def is_window_visible(self):
        # I don't know why, but WND_PROP_VISIBLE does not seem to work :(
        return cv2.getWindowProperty("sky", cv2.WND_PROP_AUTOSIZE) == 1

    def run(self):
        fps = 25.0 # seconds
        ms_delay = int(1000/fps) # milliseconds per frame
        self.update()
        while self.is_window_visible():
            ch = chr(cv2.waitKey(ms_delay) & 0xFF)
            if ch == 'q':
                break


def main():
    sim = Simulation()
    sim.run()

if __name__ == '__main__':
    main()
