import io
import logging
import SocketServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import time
from mycamera import MyCamera

PAGE="""\
<html>
<head>
<title>Raspberry Pi - Camera</title>
</head>
<body>
<center><h1>Raspberry Pi - Camera</h1></center>
<center><img src="stream.mjpg" width="640" height="480"></center>
</body>
</html>
"""


def stream_camera(server):
    cap = MyCamera(0)
    while True:
        jpg_array = cap.read_jpg()
        frame = buffer(jpg_array)[:]
        ## with open('frame.jpg') as f:
        ##     frame = f.read()
        server.wfile.write(b'--FRAME\r\n')
        server.send_header('Content-Type', 'image/jpeg')
        server.send_header('Content-Length', len(frame))
        server.end_headers()
        server.wfile.write(frame)
        server.wfile.write(b'\r\n')


class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                stream_camera(self)
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(SocketServer.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    address = ('', 8000)
    server = StreamingServer(address, StreamingHandler)
    print 'Server Started'
    server.serve_forever()
