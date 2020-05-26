import sys
import time
import datetime
import subprocess
import os
from urllib.parse import parse_qs

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


def now():
    return datetime.datetime.now().time()

class PolarisApp:

    def __init__(self, videofile=None):
        self.videofile = videofile
        if videofile is not None:
            print('FAKE CAMERA from %s' % videofile)

    def __call__(self, env, start_response):
        """
        Handle a request
        """
        self.env = env
        self.start_response = start_response
        self.parse_query_string()
        path = env['PATH_INFO']
        if path[-1] != '/':
            path += '/'
        print('Handling', path)
        if path.startswith('/camera/liveview/'):
            return self.gphoto_liveview(path)
        elif path.startswith('/camera/picture/'):
            return self.gphoto_picture(path)
        elif path.startswith('/picamera/'):
            return self.picamera(path)
        elif path == '/counter/':
            return self.counter()
        else:
            return self.hello(path)

    def parse_query_string(self):
        # parse_qs returns a LIST for every value; here, we extract values out
        # of the list
        qs = parse_qs(self.env['QUERY_STRING'])
        self.qs = {}
        for key, value in qs.items():
            self.qs[key] = value[0]

    def hello(self, path):
        http_status = '200 OK'
        headers = [('Content-Type', 'text/plain')]
        self.start_response(http_status, headers)
        path = path.encode('utf-8')
        return [b'Hello World: %s\n' % path]

    def counter(self):
        def lines():
            for i in range(10):
                yield b'Line %4d\n' % i
                time.sleep(0.5)
        http_status = '200 OK'
        headers = [('Content-Type', 'text/event-stream')]
        self.start_response(http_status, headers)
        return lines()

    def parse_picamera(self, path):
        # XXX: we should handle errors somehow
        # path is something like '/camera/raw/640x480/'
        parts = path.split('/')
        assert len(parts) == 5
        root, camera, fmt, resolution, trail = parts
        assert root == ''
        assert camera == 'picamera'
        assert trail == ''
        assert fmt in ('raw', 'mjpg')
        w, h = resolution.split('x')
        w = int(w)
        h = int(h)
        fps = self.qs.get('fps', '10')
        shutter = self.qs.get('shutter', None) # shutter speed, in seconds
        if shutter:
            shutter = int(float(shutter) * 10**6)
        return fmt, w, h, fps, shutter

    def serve_videofile(self, fname):
        # we assume it's a mjpg for now. Serve full frames at a constant rate
        headers = [
            ('Content-Type', 'video/x-motion-jpeg'),
        ]
        self.start_response('200 OK', headers)
        FPS = 5.0
        data = b''
        nframes = 0
        with open(fname, 'rb') as f:
            while True:
                chunk = f.read(1024)
                if chunk == b'':
                    return
                data += chunk
                a = data.find(b'\xff\xd8') # jpg_start
                b = data.find(b'\xff\xd9') # jpg_end
                if a != -1 and b != -1:
                    # found a new frame!
                    nframes += 1
                    print('Got frame %d' % nframes)
                    jpg_data = data[a:b+2]
                    data = data[b+2:]
                    yield jpg_data
                    time.sleep(1/FPS)


    def gphoto_liveview(self, path):
        if self.videofile is not None:
            # for testing
            yield from self.serve_videofile(self.videofile)
            return

        # gphoto2 camera
        cmd = ['gphoto2',
               #'--port', 'ptpip:192.168.1.180',
               '--capture-movie',
               '--stdout'
        ]
        print('Executing: %s' % ' '.join(cmd))
        p = subprocess.Popen(cmd, bufsize=0, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        #
        # If gphoto2 can't find the camera, it prints some text on stdout. To
        # catch the case, we try to read some bytes: if out1 is empty, it
        # means that gphoto is not streaming and out0 contains the error
        # message. Else, out0 and out1 contains "real" MJPG frames, which we
        # need to yield to the client.
        out0 = p.stdout.read(1024)
        out1 = p.stdout.read(1024)
        if out1 == b'':
            # gphoto is not streaming anything, so it must be an error
            stderr = p.stderr.read()
            p.wait()
            self.start_response('400 Bad Request', [])
            yield stderr
            yield out0
            return
        #
        # if we are here, gphoto is streaming correctly, let's read the frames
        headers = [
            ('Content-Type', 'video/x-motion-jpeg'),
        ]
        self.start_response('200 OK', headers)
        # yield the small data that we read preemptively
        yield out0
        yield out1
        # yield the rest
        try:
            # I measured that a single frame is ~54k (but maybe it will be
            # smaller if you shoot the dark sky?). We want a frame size which
            # is small enough to avoid waiting for multiple frames, but if
            # it's too small the rpi0 CPU can't handle all the work and we get
            # very few FPS. The following value seems to work well empirically
            frame_size = 1024 * 16
            while True:
                data = p.stdout.read(frame_size)
                if data == b'':
                    # gphoto stopped streaming, something is wrong?
                    break
                yield data
        finally:
            self.terminate(p)
            # make sure to unlock the camera at the end
            os.system('gphoto2 --set-config output=TFT')

    def gphoto_picture(self, path):
        headers = []
        self.start_response('404 NOT FOUND', headers)
        return []

    def picamera(self, path):
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
        self.start_response('200 OK', headers)
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
            self.terminate(p)

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


    def terminate(self, p, timeout=1):
        """
        Terminate gracefully the given process, or kill
        """
        print('Sending SIGTERM...')
        try:
            p.terminate()
            p.wait(timeout)
        except subprocess.TimeoutExpired:
            print('Timeout :(, killing the process')
            p.kill()
        else:
            print('Process successully terminated')

def main(fname):
    from wsgiref.simple_server import make_server
    app = PolarisApp(fname)
    httpd = make_server('', 8000, app)
    print("Serving HTTP on port 8000...")
    httpd.serve_forever()
    #httpd.handle_request() # serve one request, then exit

if __name__ == "__main__":
    if len(sys.argv) == 2:
        fname = sys.argv[1]
    else:
        fname = None
    main(fname)
