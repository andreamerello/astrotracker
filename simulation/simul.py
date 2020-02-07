import math
import cv2
import numpy as np
from stars import STARS, SkyPoint

def pol2cart(rho, phi):
    x = rho * np.cos(phi)
    y = rho * np.sin(phi)
    return x, y

class Sky(object):

    # by default, show the sky from -45 to +45
    def __init__(self, width, dec_width=np.pi/2):
        self.width = width
        self.dec_width = dec_width
        self.img = np.zeros(shape=[self.width, self.width, 3], dtype=np.uint8)
        self.clear()

    def radec2xy(self, ra, dec):
        # center on the north pole
        if dec < 0:
            dec += np.pi/2
        else:
            dec -= np.pi/2
        rho = dec / self.dec_width # scale to the appropriate declination width
        phi = -ra
        return pol2cart(rho, phi)

    def clear(self):
        self.img.fill(0)

    def set(self, p, color):
        x, y = self.radec2xy(p.ra, p.dec)
        self.set_cartesian(x, y, color)

    def set_cartesian(self, x, y, color):
        # x, y are in range -1..1. Tranform to image coordinates
        x = (x+1) * (self.width/2)
        y = (y+1) * (self.width/2)
        x = int(x)
        y = int(y)
        self.img[x, y] = color

    def draw_parallel(self, dec, step=0.1):
        for ra in np.arange(0, np.pi*2, step):
            p = SkyPoint(ra=ra, dec=dec)
            self.set(p, [255, 120, 120])

    def draw_meridian(self, ra, step=0.01):
        for dec in np.arange(-self.dec_width/2, self.dec_width/2, step):
            p = SkyPoint(ra=ra, dec=dec)
            self.set(p, [255, 120, 120])


class Simulation(object):

    def __init__(self):
        cv2.namedWindow("sky")
        self.sky = Sky(1000)

    def update(self):
        self.sky.clear()
        self.sky.set(SkyPoint(0, 0), color=[0, 0, 255])
        self.sky.draw_parallel(np.deg2rad(85))
        self.sky.draw_parallel(np.deg2rad(80))
        self.sky.draw_parallel(np.deg2rad(75))
        self.sky.draw_parallel(np.deg2rad(70))
        ## self.sky.draw_meridian(0)
        ## self.sky.draw_meridian(np.deg2rad(15)) # 1h
        for star in STARS:
            self.sky.set(star, color=[0, 255, 255])
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
