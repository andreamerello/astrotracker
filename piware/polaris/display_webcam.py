#!/usr/bin/python3

import sys
import cv2
from glob import glob
from mycamera import MyCamera

def save_jpg(image, fname):
    retval, jpg = cv2.imencode('.jpg', image)
    if not retval:
        raise Exception("imencode failed")
    files = glob(fname + '*.jpg')
    n = len(files)
    fname = '%s%03d.jpg' % (fname, n)
    with open(fname, 'wb') as f:
        f.write(jpg)
    return fname
    

def main():
    with MyCamera(1, rot180=True) as cam:
        while(True):
            frame = cam.read()
            #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Display the resulting frame
            cv2.imshow('frame', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                fname = save_jpg(frame, 'snapshot')
                print('Saved snapshot', fname)

    cv2.destroyAllWindows()

main()
