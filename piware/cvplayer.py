"""
An opencv-based player for the polaris app
"""

import time
import cv2
import numpy as np
import requests

def counter():
    resp = requests.get('http://polaris.local:8000/counter/', stream=True)
    for chunk in resp.iter_content(10):
        print(chunk)

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


def get_frames_requests(url, chunk_size):
    resp = requests.get(url, stream=True)
    yield from resp.iter_content(chunk_size)


def get_frames_raw_connection(url, chunk_size):
    import socket
    conn = socket.create_connection(('polaris.local', 8000))
    conn.send(b'GET /camera?w=320&h=240&fps=2 HTTP/1.0\r\n')
    conn.send(b'\r\n')
    data = conn.recv(200) # XXX: we should read until we find the empty
                          # newline, check the status, parse the headers, etc.

    data = b''
    while True:
        chunk = conn.recv(chunk_size)
        data += chunk
        if len(data) > chunk_size:
            # got a full frame
            yield data[:chunk_size]
            data = data[chunk_size:]


def main():
    W, H, fps = 320, 240, 2
    ## W, H, fps = 640, 480,  5
    ## W, H, fps = 2592, 1944, 1

    W, H = raw_resolution(W, H)
    URL = 'http://polaris.local:8000/camera?'
    URL += 'w=%s&h=%s&fps=%s' % (W, H, fps)
    #URL += '&shutter=5'

    ## URL = 'http://localhost:8000/camera?w=640&h=480'

    #frames = get_frames_requests(URL, chunk_size=W*H)
    frames = get_frames_raw_connection(URL, chunk_size=W*H)

    tstart = time.time()
    for i, data in enumerate(frames):
        print('[%5.2f] got frame: %d' % (time.time()-tstart, i))
        frame = np.frombuffer(data, dtype=np.uint8).reshape(H, W)
        cv2.imshow("frame", frame)
        ch = chr(cv2.waitKey(1) & 0xFF)
        if ch == 'q':
            break


def raw_connection():
    import socket
    conn = socket.create_connection(('polaris.local', 8000))
    conn.send(b'GET /camera?w=320&h=240&fps=2 HTTP/1.0\r\n')
    conn.send(b'\r\n')
    data = conn.recv(200)
    print(data.decode('utf-8'))
    print(len(data))
    print()
    Y_LEN = 320*240
    bytes_read = 0
    i = 0
    tstart = time.time()
    while True:
        data = conn.recv(Y_LEN)
        bytes_read += len(data)
        if bytes_read > Y_LEN:
            # got a full frame
            print('[%5.2f] got frame: %d' % (time.time()-tstart, i))
            i += 1
            bytes_read -= Y_LEN



if __name__ == '__main__':
    main()
    #raw_connection()
