import os
import time
import subprocess
from utils import terminate
from pathlib import Path

class GPhotoCamera:

    # XXX find this programmatically:
    #    gphoto2 --list-folders
    CAMERA_FOLDER = '/store_00020001/DCIM/100CANON/'
    CAPTURE_DIR = Path('/tmp/pictures')

    def __init__(self, app, videofile):
        self.app = app
        self.videofile = videofile
        self.CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

    def liveview(self, path):
        if self.videofile is not None:
            # for testing
            yield from self.serve_videofile(self.videofile)
            return

        # gphoto2 camera
        cmd = ['gphoto2',
               #'--port', 'ptpip:192.168.1.180',
               '--set-config', 'output=TFT + PC',
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
            self.app.start_response('400 Bad Request', [])
            yield stderr
            yield out0
            return
        #
        # if we are here, gphoto is streaming correctly, let's read the frames
        headers = [
            ('Content-Type', 'video/x-motion-jpeg'),
        ]
        self.app.start_response('200 OK', headers)
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
            terminate(p)
            # make sure to unlock the camera at the end
            os.system('gphoto2 --set-config output=TFT')

    def serve_videofile(self, fname):
        # we assume it's a mjpg for now. Serve full frames at a constant rate
        headers = [
            ('Content-Type', 'video/x-motion-jpeg'),
        ]
        self.app.start_response('200 OK', headers)
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

    def picture(self, path):
        """
        Retrieve a picture from the camera. The url is something like:
            /camera/picture/IMG_1234.JPG
        """
        root, camera, picture, fname = path.split('/', 3)
        assert root == ''
        assert camera == 'camera'
        assert picture == 'picture'
        if fname[-1] == '/':
            fname = fname[:-1]
        if '/' in fname:
            self.app.start_response('400 Bad Request', [])
            return [b'Invalid filename: %s' % fname.encode('utf-8')]

        fpath = self.CAPTURE_DIR / fname
        if fpath.exists():
            print('%s already exists, serving directly' % fpath)
        else:
            os.chdir(str(self.CAPTURE_DIR))
            cmd = [
                'gphoto2',
                '--force-overwrite',
                '--folder', self.CAMERA_FOLDER,
                '--get-file', fname
            ]
            print('Executing: %s' % ' '.join(cmd))
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if proc.returncode != 0:
                self.app.start_response('400 Bad Request', [])
                return [proc.stdout]

        content = fpath.read_bytes()
        headers = [
            ('Content-Type', 'image/jpeg'),
            ('Content-Disposition', 'inline; filename="%s"' % fname),
            ('Content-Length', str(len(content))),
        ]
        self.app.start_response('200 OK', headers)
        return [content]
