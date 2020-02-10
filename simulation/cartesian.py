import cv2
import numpy as np
from cvextra import CvTrackbar

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (255, 0, 0)
RED = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (0, 255, 255)
CYAN = (255, 255, 0)
MAGENTA = (255, 0 , 255)

class Image:
    """
    OpenCV image which represents a cartesian plane.

    The origin is at the center of the image, the Y axis goes from bottom to
    top.

    The size of the image is pixel_width, the size of the plane is
    unit_width. So, if unit_width == 1.0, the top-left corner is (-0.5, 0.5),
    the bottom-right is (0.5, -0.5)

                    TL        ^
                              |
                              |
                              |
                              |
                              |
                    ----------+---------->
                              |
                              |
                              |
                              |
                              |         BR
    """

    def __init__(self, pixel_width, unit_width):
        self.pixel_width = pixel_width
        self.unit_width = unit_width
        self.zoom = 1.0
        self.mat = np.zeros(shape=[pixel_width, pixel_width, 3], dtype=np.uint8)

    @property
    def pixels_per_unit(self):
        return self.pixel_width / self.unit_width * self.zoom

    def clear(self):
        self.mat.fill(0)

    def _convert(self, p):
        W = self.pixel_width
        x, y = p
        i = x * self.pixels_per_unit + W/2
        j = -y * self.pixels_per_unit + W/2
        return int(i), int(j)

    def set(self, p, color):
        i, j = self._convert(p)
        if 0 <= i < self.pixel_width and 0 <= j < self.pixel_width:
            # note, we need to use j, i because matrices are in row-order
            self.mat[j, i] = color

    def line(self, p1, p2, color):
        p1 = self._convert(p1)
        p2 = self._convert(p2)
        cv2.line(self.mat, p1, p2, color)


class Window:
    """
    An OpenCV window which shows a CartesianImage
    """

    def __init__(self, name, img, redraw_fn):
        self.name = name
        self.img = img
        self.redraw_fn = redraw_fn
        cv2.namedWindow(name)
        self.zoom = CvTrackbar('zoom', self.name, 1, 10, self.on_zoom)

    def on_zoom(self, value):
        if value == 0:
            self.zoom.value = 1
            return
        self.img.zoom = value
        self.show()

    def show(self):
        self.redraw_fn()
        cv2.imshow(self.name, self.img.mat)




if __name__ == '__main__':
    plane = Image(1000, 1.0)
    def redraw_fn():
        plane.clear()
        plane.line((-0.5, 0), (0.5, 0), YELLOW)  # X axis
        plane.line((0, -0.5), (0, 0.5), MAGENTA) # Y axis
        plane.set((0, 0), WHITE)                 # origin
        plane.set((0.4, 0.1), YELLOW)
        for y in np.arange(-0.5, 0.5, 0.05):
            plane.set((0.1, y), RED)

    win = Window('plane', plane, redraw_fn)
    win.show()
    cv2.waitKey(0)
