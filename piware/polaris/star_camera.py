import time
import traceback
import io
import threading
import picamera


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = threading.Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StarCamera(object):

    def __init__(self, shutter_speed=1):
        self.camera = picamera.PiCamera(resolution='2592x1952')
        #self.camera.ISO = 800
        self.output = StreamingOutput()
        self.set_shutter_speed(shutter_speed)

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
        except Exception as e:
            print('Exception inside set_shutter_speed')
            traceback.print_exc()
            print()
            print()

    def _start_recording(self):
        #self.camera.start_recording(self.analyzer, 'rgb')
        self.camera.start_recording(self.output, format='mjpeg')

    def read_frames(self):
        with self.camera:
            speed = self.camera.shutter_speed / 10**6
            self.camera.start_preview()
            self._start_recording()
            #
            # empirically, we need to wait 6 frames before we can see anything
            wait_time = (self.camera.shutter_speed / 10**6) * 6
            wait_time = max(wait_time, 2) # at least to seconds
            print('Waiting %.2fs for camera to warm up...' % wait_time)
            time.sleep(wait_time)
            last_frame = time.time()
            while True:
                with self.output.condition:
                    self.output.condition.wait()
                    frame = self.output.frame
                ## now = time.time()
                ## fps = 1.0 / (now - last_frame)
                ## exposure = self.camera.exposure_speed / 1000
                ## shutter = self.camera.shutter_speed / 1000
                ## print('fps=%.2f iso=%s  analog=%.2f  digital=%.2f   exposure=%dms   shutter=%dms' % (fps, self.camera.iso, self.camera.analog_gain, self.camera.digital_gain, exposure, shutter))
                yield frame

    def example(self):
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
                            print('changing the shutter speed on the fly')
                            self.set_shutter_speed(1)
                finally:
                    self.camera.stop_recording()

def main():
    star_camera = StarCamera()
    star_camera.example()

if __name__ == '__main__':
    main()
