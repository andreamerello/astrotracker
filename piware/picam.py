import os
import subprocess
import time
from utils import now, terminate

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

class PiCamera:
    def __init__(self, app):
        self.app = app

    def parse_picamera(self, path):
        # XXX: we should handle errors somehow
        # path is something like '/picamera/liveview/raw/640x480/'
        parts = path.split('/')
        assert len(parts) == 6
        root, camera, lv, fmt, resolution, trail = parts
        assert root == ''
        assert camera == 'picamera'
        assert lv == 'liveview'
        assert trail == ''
        assert fmt in ('raw', 'mjpg')
        w, h = resolution.split('x')
        w = int(w)
        h = int(h)
        fps = self.app.qs.get('fps', '10')
        shutter = self.app.qs.get('shutter', None) # shutter speed, in seconds
        if shutter:
            shutter = int(float(shutter) * 10**6)
        return fmt, w, h, fps, shutter

    def liveview(self, path):
        fmt, w, h, fps, shutter = self.parse_picamera(path)
        w, h = raw_resolution(w, h)
        if fmt == 'raw':
            headers = [
                ('Content-Type', 'video/x-raw'),
                ('X-Width', str(w)),
                ('X-Height', str(h)),
            ]
        elif fmt == 'mjpg':
            headers = [
                ('Content-Type', 'video/x-motion-jpeg'),
            ]
        self.app.start_response('200 OK', headers)
        return self.frames_from_raspivid(fmt, w, h, fps, shutter)
        #return fromfile('/home/pi/video.yuv', 'raw', w*h)

    def frames_fromfile(self, fname, fmt, frame_size):
        with open(fname, 'rb') as f:
            yield from self.getframes(f, fmt, frame_size)

    def frames_from_raspivid(self, fmt, w, h, fps, shutter):
        if fmt == 'raw':
            cmd = ['raspividyuv', '--luma'] # stream only the Y (luminance) data
            frame_size = w*h
        elif fmt == 'mjpg':
            cmd = ['raspivid', '-cd', 'MJPEG']
            # we don't have a fixed frame size, stream the data in chunks of 1k
            frame_size = 1024

        cmd += ['-t', '0', # no timeout, record forever
                '-w', str(w),
                '-h', str(h),
                '-fps', fps,
                '-o', '-']
        if shutter:
            cmd += [
                '-ss', str(shutter)
                ]
        print('Executing: %s' % ' '.join(cmd))
        p = subprocess.Popen(cmd, bufsize=0, stdout=subprocess.PIPE)
        try:
            yield from self.getframes(p.stdout, fmt, frame_size)
        finally:
            terminate(p)

    def getframes(self, f, fmt, frame_size):
        tstart = time.time()
        i = 0
        bytes_read = 0
        while True:
            data = f.read(frame_size)
            if data == b'':
                print('getframes EOF')
                break
            bytes_read += len(data)
            if fmt == 'raw' and bytes_read > frame_size:
                # got a full frame
                print('[%5.2f %s] got frame: %d' % (time.time()-tstart, now(), i))
                i += 1
                bytes_read -= frame_size
            yield data
