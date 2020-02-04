import time
import datetime
import subprocess
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
        if path == '/camera/yuv/':
            return self.camera('yuv')
        if path == '/camera/jpg/':
            return self.camera('jpg')
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
        return [b'Hello World: %s' % path]

    def counter(self):
        def lines():
            for i in range(10):
                yield b'Line %4d\n' % i
                time.sleep(0.5)
        http_status = '200 OK'
        headers = [('Content-Type', 'text/event-stream')]
        self.start_response(http_status, headers)
        return lines()

    def camera(self, fmt):
        w = int(self.qs.get('w', 2592))
        h = int(self.qs.get('h', 1944))
        w, h = raw_resolution(w, h)
        #
        fps = self.qs.get('fps', '10')
        shutter = self.qs.get('shutter', None) # shutter speed, in seconds
        if shutter:
            shutter = int(float(shutter) * 10**6)
        #
        http_status = '200 OK'
        headers = [('Content-Type', 'application/octet-stream')]
        self.start_response(http_status, headers)
        return self.frames_fromcamera(fmt, w, h, fps, shutter)
        #return fromfile('/home/pi/video.yuv', 'yuv', w*h)

    def frames_fromfile(self, fname, fmt, frame_size):
        with open(fname, 'rb') as f:
            yield from self.getframes(f, fmt, frame_size)

    def frames_fromcamera(self, fmt, w, h, fps, shutter):
        if fmt == 'yuv':
            cmd = ['raspividyuv', '--luma'] # stream only the Y (luminance) data
            frame_size = w*h
        elif fmt == 'jpg':
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
            bytes_read += len(data)
            if fmt == 'yuv' and bytes_read > frame_size:
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

def main():
    from wsgiref.simple_server import make_server
    app = PolarisApp()
    httpd = make_server('', 8000, app)
    print("Serving HTTP on port 8000...")
    httpd.serve_forever()
    #httpd.handle_request() # serve one request, then exit

if __name__ == "__main__":
    main()
