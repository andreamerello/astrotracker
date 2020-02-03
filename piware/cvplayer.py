"""
An opencv-based player for the polaris app
"""

import cv2
import numpy as np
import requests

def counter():
    resp = requests.get('http://polaris.local:8000/counter/', stream=True)
    for chunk in resp.iter_content(10):
        print(chunk)

# stolen from picamera
def raw_resolution(width, height, splitter=False):
    """
    Round a (width, height) tuple up to the nearest multiple of 32 horizontally
    and 16 vertically (as this is what the Pi's camera module does for
    unencoded output).
    """
    if splitter:
        fwidth = (width + 15) & ~15
    else:
        fwidth = (width + 31) & ~31
    fheight = (height + 15) & ~15
    return fwidth, fheight


def main():
    ## W, H = 320, 240
    ## fps = 10

    W, H = 640, 480
    fps = 5

    W, H = raw_resolution(W, H)
    URL = 'http://polaris.local:8000/camera?'
    URL += 'w=%s&h=%s&fps=%s' % (W, H, fps)

    ylen = W*H
    resp = requests.get(URL, stream=True)
    for i, data in enumerate(resp.iter_content(ylen)):
        print('Got frame: %d' % i)
        frame = np.frombuffer(data, dtype=np.uint8).reshape(H, W)
        cv2.imshow("frame", frame)
        ch = chr(cv2.waitKey(1) & 0xFF)
        if ch == 'q':
            break


if __name__ == '__main__':
    main()
