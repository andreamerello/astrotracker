import subprocess
import datetime

def terminate(p, timeout=1):
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

def now():
    return datetime.datetime.now().time()

def iter_mjpg(f, data=b''):
    """
    Iterates over all the frames in a MJPG stream
    """
    # I measured that a single frame is ~54k (but maybe it will be
    # smaller if you shoot the dark sky?). We want a frame size which
    # is small enough to avoid waiting for multiple frames, but if
    # it's too small the rpi0 CPU can't handle all the work and we get
    # very few FPS. The following value seems to work well empirically
    chunk_size = 1024 * 16
    while True:
        chunk = f.read(chunk_size)
        if chunk == b'':
            return
        data += chunk
        a = data.find(b'\xff\xd8') # jpg_start
        b = data.find(b'\xff\xd9') # jpg_end
        if a != -1 and b != -1:
            jpg_data = data[a:b+2]
            data = data[b+2:]
            yield jpg_data
