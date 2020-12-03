import sys
import time
import datetime
import subprocess
import os
from urllib.parse import parse_qs
from gphotocam import GPhotoCamera
from picam import PiCamera

class PolarisApp:

    def __init__(self, fake_camera_file=None):
        if fake_camera_file is not None:
            print('FAKE CAMERA from %s' % fake_camera_file)
        self.gphoto = GPhotoCamera(self, fake_camera_file)
        self.picam = PiCamera(self)

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
        #print('Handling', path)
        if path.startswith('/camera/liveview/'):
            return self.gphoto.liveview(path)
        elif path.startswith('/camera/picture/'):
            return self.gphoto.picture(path)
        elif path.startswith('/camera/unlock/'):
            return self.gphoto.unlock(path)
        elif path.startswith('/picamera/liveview/'):
            return self.picam.liveview(path)
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

def patch_handler():
    # hack to avoid logging all requests to /camera/liveview: we log only the first
    from wsgiref.simple_server import WSGIRequestHandler
    def log_request(self, code='-', size='-'):
        if self.requestline == WSGIRequestHandler.last_requestline == 'GET /camera/liveview/ HTTP/1.1':
            return
        WSGIRequestHandler.last_requestline = self.requestline
        super(WSGIRequestHandler, self).log_request(code, size)

    WSGIRequestHandler.last_requestline = None
    WSGIRequestHandler.log_request = log_request


def main(fname):
    from wsgiref.simple_server import make_server
    patch_handler()
    app = PolarisApp(fname)
    httpd = make_server('', 8000, app)
    print("Serving HTTP on port 8000...")
    httpd.serve_forever()
    #httpd.handle_request() # serve one request, then exit

if __name__ == "__main__":
    if len(sys.argv) == 2:
        fake_camera_file = sys.argv[1]
    else:
        fake_camera_file = None
    main(fake_camera_file)
