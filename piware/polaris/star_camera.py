import time
import traceback
import picamera
import numpy as np
from picamera.array import PiRGBAnalysis

class StarAnalyzer(PiRGBAnalysis):
    def __init__(self, camera):
        super(StarAnalyzer, self).__init__(camera)
        self.last_frame = time.time()

    def analyze(self, frame):
        now = time.time()
        fps = 1.0 / (now - self.last_frame)
        exposure = self.camera.exposure_speed / 1000
        shutter = self.camera.shutter_speed / 1000
        print 'fps=%.2f iso=%s  analog=%s  digital=%s   exposure=%dms   shutter=%dms' % (fps, self.camera.iso, self.camera.analog_gain, self.camera.digital_gain, exposure, shutter)
        self.last_frame = now



class StarCamera(object):

    def __init__(self):
        self.camera = picamera.PiCamera(resolution='2592x1952')
        self.camera.ISO = 800
        self.analyzer = StarAnalyzer(self.camera)
        self.set_shutter_speed(0.5)

    def set_shutter_speed(self, speed):
        """
        speed is in seconds
        """
        try:
            recording = self.camera.recording
            if recording:
                self.camera.stop_recording()
            #
            self.camera.framerate = 1.0 / speed
            self.camera.shutter_speed = int(speed * (1000 * 1000))
            #
            if recording:
                self._start_recording()
        except Exception, e:
            print 'Exception inside set_shutter_speed'
            traceback.print_exc()
            print
            print

    def _start_recording(self):
        self.camera.start_recording(self.analyzer, 'rgb')

    def start(self):
        with self.camera:
            # TODO: think about awb gains
            ## camera.awb_mode = 'off'
            ## camera.awb_gains = (1.4, 1.5)

            self.camera.start_preview()
            with self.analyzer:
                self._start_recording()
                try:
                    i = 0
                    while True:
                        i += 1
                        self.camera.wait_recording(1)
                        if i == 5:
                            print 'changing the shutter speed on the fly'
                            self.set_shutter_speed(1)
                finally:
                    self.camera.stop_recording()

def main():
    star_camera = StarCamera()
    star_camera.start()

if __name__ == '__main__':
    main()
