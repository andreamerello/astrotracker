import time
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
        if path == '/camera/':
            return self.camera()
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

    def camera(self):
        w = int(self.qs.get('w', 2592))
        h = int(self.qs.get('h', 1944))
        w, h = raw_resolution(w, h)
        #
        fps = self.qs.get('fps', 1)
        shutter = self.qs.get('shutter', None) # shutter speed, in seconds
        #
        Y_LEN = w*h
        UV_LEN = (w//2) * (h//2) * 2

        def fromfile(fname):
            with open(fname, 'rb') as f:
                yield from getframes(f)

        def fromcamera():
            cmd = ['raspividyuv',
                   '-t', '0', # no timeout, record forever
                   '-w', str(w),
                   '-h', str(h),
                   '-fps', fps,
                   '-o', '-']
            if shutter:
                cmd += [
                    '-ss', str(shutter * 10**6)
                    ]
            p = subprocess.Popen(cmd, bufsize=Y_LEN+UV_LEN, stdout=subprocess.PIPE)
            yield from getframes(p.stdout)

        def getframes(f):
            while True:
                ydata = f.read(Y_LEN) # read luminance
                if ydata == '':
                    break
                assert len(ydata) == Y_LEN
                uvdata = f.read(UV_LEN) # read and discard chrominance
                assert len(uvdata) == UV_LEN
                yield ydata

        http_status = '200 OK'
        headers = [('Content-Type', 'application/octet-stream')]
        self.start_response(http_status, headers)
        return fromcamera()
        #return fromfile('/home/pi/video.yuv')



def main():
    from wsgiref.simple_server import make_server
    app = PolarisApp()
    httpd = make_server('', 8000, app)
    print("Serving HTTP on port 8000...")
    httpd.serve_forever()
    #httpd.handle_request() # serve one request, then exit

if __name__ == "__main__":
    main()
