from __future__ import print_function
import sys
import threading, time

print('Loading cv2...', end='')
sys.stdout.flush()
import cv2
print(cv2.__version__)

# try also this
#v4l2-ctl -d /dev/video1 -c exposure_auto=1 -c exposure_auto_priority=0 -c exposure_absolute=10

# bufferless VideoCapture, inspired by
# https://stackoverflow.com/questions/43665208/how-to-get-the-latest-frame-from-capture-device-camera-in-opencv-python
class MyCamera:

    def __init__(self, videoname):
        self._videoname = videoname
        self.cap = None
        self._lastframe = None
        self._newframe = threading.Event()
        self._t = None

    def _start(self):
        self.cap = cap = cv2.VideoCapture()
        cap.open(self._videoname, apiPreference=cv2.CAP_V4L2)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        ## cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        ## cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        ## cap.set(cv2.CAP_PROP_FPS, 30.0)
        self._t = threading.Thread(target=self._reader)
        self._t.daemon = True
        self._t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while self.cap:
            ret, frame = self.cap.read()
            if not ret:
                print("Cannot read from self.cap, exiting")
                break
            self._lastframe = frame
            self._newframe.set()

    def read(self):
        self._newframe.wait()
        self._newframe.clear()
        return self._lastframe

    def read_jpg(self):
        frame = self.read()
        retval, jpg = cv2.imencode('.jpg', frame)
        if not retval:
            raise Exception("imencode failed")
        return jpg

    def __enter__(self):
        self._start()
        return self

    def __exit__(self, etype, evalue, tb):
        print('release')
        self.cap.release()
        self.cap = None


if __name__ == '__main__':
    cap = VideoCapture(0)
    while True:
        time.sleep(.5)   # simulate time between events
        frame = cap.read()
        cv2.imshow("frame", frame)
        if chr(cv2.waitKey(1)&255) == 'q':
            break
