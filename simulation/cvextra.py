import cv2

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
