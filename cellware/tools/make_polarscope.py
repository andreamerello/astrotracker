#!/usr/bin/python3

"""
NOTE: at the moment this is not meant to be run inside kivy. Instead, you
should run it offline (with python3) to generate various images to be used as
polar scopes.
"""

import math
from dataclasses import dataclass
import PIL.Image
import PIL.ImageDraw
from . import stars

@dataclass
class SkyPoint:
    ra: float
    dec: float
    name: str = ''

    def __str__(self):
        d_ra = math.degrees(self.ra)
        d_dec = math.degrees(self.dec)
        return f'(ra={d_ra:6.2f}°, dec={d_dec:6.2f}°)'

@dataclass
class Star(SkyPoint):
    hipparcos: int = -1
    magnitude: float = -1



PI = math.pi
NORTH_POLE = SkyPoint(0, PI/2, name='North Pole')

class Sky:
    """
    Different kind of coordinates used:

      - sky coordinates: RA/DEC, see SkyPoint
      - image coordinates: (0, 0) is the upper-left, Y axis goes downward
      - plane coordinates: (0, 0) is the center, Y axis goes upward
    """

    CENTER = NORTH_POLE

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.pixel_width = 1.0 / width
        self.im = PIL.Image.new('RGB', (width, height))
        self._draw = PIL.ImageDraw.Draw(self.im)

    def _plane2img(self, p):
        x, y = p
        i = x + self.width/2
        j = self.height/2 - y
        return i, j

    def _sky2img(self, p):
        x, y = self._sky2plane(p)
        return self._plane2img((x, y))

    def _sky2plane(self, p):
        """
        Orthographic azimuthal projection, as described here:
        http://www.projectpluto.com/project.htm

        Argument: a SkyPoint point with ra and dec expressed in radians
        Return value: a (x, y) tuple whose values range from -1.0 to 1.0
                      -1.0 is -PI/2
                       1.0 is  PI/2
        """
        from math import sin, cos
        CENTER = self.CENTER
        delta_ra = p.ra - CENTER.ra
        # x, y are in the range (-1.0, 1.0)
        #                        -1.0 is -PI/2
        #                         1.0 is  PI/2
        x = cos(p.dec) * sin(delta_ra)
        y = sin(p.dec) * cos(CENTER.dec) - cos(p.dec) * cos(delta_ra) * sin(CENTER.dec)
        #
        # transform x, y into plane coordinate
        x *= self.width/2
        y *= self.width/2
        return x, -y

    def test_plane(self):
        W, H = self.width/2, self.height/2
        c = self._plane2img
        O = (0, 0) # origin
        self._draw.line([c(O), c((0, H))], fill='yellow')  # positive Y
        self._draw.line([c(O), c((0, -H))], fill='green')  # negative Y
        self._draw.line([c(O), c((W, 0))], fill='blue')    # positive X
        self._draw.line([c(O), c((-W, 0))], fill='purple') # negative X
        self._draw.point(c(O), fill='red')                 # origin

    def test_sky(self):
        self.point(NORTH_POLE, fill='red')
        self.celestial_parallel(dec=math.radians(80))
        self.celestial_parallel(dec=math.radians(70))
        self.celestial_parallel(dec=math.radians(60))
        for hr in range(0, 23):
            self.celestial_meridian(ra=math.radians(hr*15))

    def test_stars(self):
        self.cross(NORTH_POLE, fill='red')
        for star in stars.STARS:
            self.star(star)

    def point(self, p, **kwargs):
        p1 = self._sky2img(p)
        self._draw.point(p1, **kwargs)

    def circle(self, p, radius, **kwargs):
        """
        p is a SkyPoint
        radius is in pixels
        """
        cx, cy = self._sky2img(p)
        self._draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], **kwargs)

    def cross(self, p, **kwargs):
        W = 3 # pixels
        x, y = self._sky2img(p)
        self._draw.line([(x-W, y), (x+W, y)], **kwargs)
        self._draw.line([(x, y-W), (x, y+W)], **kwargs)

    def star(self, s):
        if s.magnitude > 4:
            self.point(s, fill='yellow')
        else:
            radius = int(6-s.magnitude)
            self.circle(s, radius, outline='yellow')

    def line(self, p0, p1, **kwargs):
        p0 = self._sky2img(p0)
        p1 = self._sky2img(p1)
        self._draw.line([p0, p1], **kwargs)

    def celestial_parallel(self, dec):
        ra_steps = 0.1
        for ra in arange(0, 2*PI, ra_steps):
            self.point(SkyPoint(ra=ra, dec=dec), fill='azure')

    def celestial_meridian(self, ra):
        dec_steps = 0.1
        dec_start = self.CENTER.dec - PI/2
        dec_stop = self.CENTER.dec + PI/2
        for dec in arange(dec_start, dec_stop, dec_steps):
            self.point(SkyPoint(ra=ra, dec=dec), fill='green')


def arange(start, stop, step):
    if stop < start:
        return
    i = start
    while i < stop:
        yield i
        i += step


def main():
    W = 1280
    H = 960
    sky = Sky(W, H)

    #sky.test_plane()
    sky.test_sky()
    sky.test_stars()

    scale = 1
    im = sky.im.resize((W*scale, H*scale), resample=PIL.Image.BILINEAR)
    im.show()
    #sky.im.save('foo.png')


if __name__ == '__main__':
    main()
