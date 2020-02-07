import math
import cv2
import numpy as np
from stars import STARS, SkyPoint

def find_star(n):
    for s in STARS:
        if s.hipparcos == n:
            return s
    raise KeyError(n)

KOCHAB = find_star(72607)

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y

class Sky:

    # by default, show the sky from -45 to +45
    def __init__(self, width, dec_width=np.pi/2):
        self.width = width
        self.dec_width = dec_width
        self.time = 0
        self.angular_speed = np.pi*2 / (24*60*60) # 360 deg in 24hrs
        self.img = np.zeros(shape=[self.width, self.width, 3], dtype=np.uint8)
        self.clear()

    def radec2xy(self, ra, dec):
        # center on the north pole
        if dec < 0:
            dec += np.pi/2
        else:
            dec -= np.pi/2
        rho = dec / self.dec_width # scale to the appropriate declination width
        #
        t_angle = self.time * self.angular_speed
        phi = -ra + t_angle
        x, y = pol2cart(rho, phi)
        #
        # x, y are in range -1..1. Tranform to image coordinates
        x = (x+1) * (self.width/2)
        y = (y+1) * (self.width/2)
        return int(x), int(y)

    def clear(self):
        self.img.fill(0)

    def set(self, p, color):
        x, y = self.radec2xy(p.ra, p.dec)
        self.set_cartesian(x, y, color)

    def set_cartesian(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.width:
            self.img[x, y] = color

    def draw_parallel(self, dec, step=0.1):
        for ra in np.arange(0, np.pi*2, step):
            p = SkyPoint(ra=ra, dec=dec)
            self.set(p, [255, 120, 120])

    def draw_meridian(self, ra, step=0.01):
        for dec in np.arange(-self.dec_width/2, self.dec_width/2, step):
            p = SkyPoint(ra=ra, dec=dec)
            self.set(p, [255, 120, 120])



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


class Camera:

    def __init__(self, ra, dec):
        self.ra = ra
        self.dec = dec
        self.horiz_angle = np.deg2rad(4.24)   # angle of view of APS-C @ 300mm
        self.vert_angle = np.deg2rad(2.83)

    def draw(self, sky):
        w = sky.width / sky.dec_width * self.horiz_angle / 2
        h = sky.width / sky.dec_width * self.vert_angle  / 2
        x, y = sky.radec2xy(self.ra, self.dec)
        p1 = int(x-w/2), int(y-h/2)
        p2 = int(x+w/2), int(y+h/2)
        cv2.rectangle(sky.img, p1, p2, [0, 255, 0])

NORTH_POLE = SkyPoint(0, np.pi/2)

class Simulation:

    def __init__(self):
        cv2.namedWindow("sky")
        self.ready = False
        self.zoom = CvTrackbar('zoom', 'sky', 1, 10, self.update)
        self.time = CvTrackbar('time', 'sky', 0, 60*60*24, self.update)
        self.sky = Sky(1000)
        self.camera = Camera(KOCHAB.ra, KOCHAB.dec)
        self.ready = True

    def update(self, value=None):
        if not self.ready:
            return
        if self.zoom.value == 0:
            self.zoom.value = 1
            return
        self.sky.dec_width = np.pi/2 / self.zoom.value
        self.sky.time = self.time.value

        self.sky.clear()
        self.sky.set(NORTH_POLE, color=[0, 0, 255])
        self.sky.draw_parallel(np.deg2rad(85))
        self.sky.draw_parallel(np.deg2rad(80))
        self.sky.draw_parallel(np.deg2rad(75))
        self.sky.draw_parallel(np.deg2rad(70))
        self.sky.draw_parallel(np.deg2rad(65))
        self.sky.draw_parallel(np.deg2rad(60))
        ## self.sky.draw_meridian(0)
        ## self.sky.draw_meridian(np.deg2rad(15)) # 1h
        for star in STARS:
            self.sky.set(star, color=[0, 255, 255])

        self.camera.draw(self.sky)
        cv2.imshow('sky', self.sky.img)

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
