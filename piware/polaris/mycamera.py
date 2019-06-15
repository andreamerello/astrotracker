import sys
import Queue, threading, time
print 'Loading cv2...',
sys.stdout.flush()
import cv2
print 'DONE'


# bufferless VideoCapture, inspired by
# https://stackoverflow.com/questions/43665208/how-to-get-the-latest-frame-from-capture-device-camera-in-opencv-python
class MyCamera:

    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)
        self.q = Queue.Queue()
        t = threading.Thread(target=self._reader)
        t.daemon = True
        t.start()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except Queue.Empty:
                    pass
            self.q.put(frame)

    def read(self):
        return self.q.get()

    def read_jpg(self):
        frame = self.read()
        retval, jpg = cv2.imencode('.jpg', frame)
        if not retval:
            raise Exception("imencode failed")
        return jpg

if __name__ == '__main__':
    cap = VideoCapture(0)
    while True:
        time.sleep(.5)   # simulate time between events
        frame = cap.read()
        cv2.imshow("frame", frame)
        if chr(cv2.waitKey(1)&255) == 'q':
            break
