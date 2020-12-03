import os
import time
import subprocess
from utils import terminate
from pathlib import Path
import threading


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



class GPhotoThread:

    def __init__(self, fake_camera_file):
        self.fake_camera_file = fake_camera_file
        self.state = 'STOPPED'
        self.thread = None
        self._latest_frame = (-1, None) # (frame_no, bytes_content)

    def start(self):
        assert self.state == 'STOPPED' # XXX todo
        self.state = 'STARTING'
        self.thread = threading.Thread(target=self.run, name='GPhotoThread.run')
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.should_stop = True

    def log(self, *args):
        print('[GPhotoThread]', *args)

    def get_latest_frame(self):
        return self._latest_frame

    def run(self):
        assert self.state == 'STARTING'
        self.should_stop = False
        if self.fake_camera_file:
            cmd = ['python3', 'fake-gphoto-capture.py', self.fake_camera_file]
        else:
            cmd = ['gphoto2',
                   #'--port', 'ptpip:192.168.1.180',
                   '--set-config', 'output=TFT + PC',
                   '--capture-movie',
                   '--stdout'
            ]
        self.log('Executing: %s' % ' '.join(cmd))
        p = subprocess.Popen(cmd, bufsize=0,
                             stdout=subprocess.PIPE,
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
            self.state = 'ERROR'
            self.error = stderr + out0
            self.running = False
            return
        #
        # if we are here, gphoto is streaming correctly, let's read the frames
        self.state = 'STREAMING'
        try:
            # XXX: kill gphoto if nobody has asked for a frame in the last X seconds
            n = 0
            for frame in iter_mjpg(p.stdout, out0+out1):
                self._latest_frame = (n, frame) # atomic update
                n += 1
                if n % 10 == 0:
                    self.log('got frame', n)
                if self.should_stop:
                    self.log('should_stop received, exiting')
                    return
        finally:
            self.log('terminating process')
            terminate(p)
            if not self.FAKE_CAPTURE:
                # make sure to unlock the camera at the end
                os.system('gphoto2 --set-config output=TFT')
            self.state = 'STOPPED'


class GPhotoCamera:

    # XXX find this programmatically:
    #    gphoto2 --list-folders
    CANON_CAMERA_FOLDER = '/store_00020001/DCIM/100CANON/'
    NIKON_CAMERA_FOLDER = '/store_00010001/DCIM/100D5300/'
    CAPTURE_DIR = Path('/tmp/pictures')

    def __init__(self, app, fake_camera_file):
        self.app = app
        self.CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        self.gphoto = GPhotoThread(fake_camera_file)

    def liveview(self, path):
        if self.gphoto.state == 'STOPPED':
            print('Starting gphoto thread')
            self.gphoto.start()
            t = time.time()
            while self.gphoto.state == 'STARTING':
                elapsed = time.time() - t
                if elapsed > 5.0:
                    return self.error(b'gphoto did not start')
                #print('    waiting...')
                time.sleep(0.1)

        if self.gphoto.state == 'ERROR':
            self.app.start_response('400 Bad Request', [])
            return [self.gphoto.error]

        if self.gphoto.state == 'STREAMING':
            # return the last frame
            n, frame = self.gphoto.get_latest_frame()
            headers = [
                ('Content-Type', 'image/jpeg'),
                ('X-Frame-Number', str(n)),
            ]
            self.app.start_response('200 OK', headers)
            return [frame]

        # if we are here, we are in an unexpected state
        return self.error('Unknown gphoto thread state: %s' % self.gphoto.state)

    def error(self, message):
        print('ERROR:', message)
        self.app.start_response('500 Internal Server Error', [])
        return [message]

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
            cmd = [ 'gphoto2',
                    '--auto-detect'
            ]
            print('Executing: %s' % ' '.join(cmd))
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if str(proc.stdout).find("Nikon") > 0:
                camera_folder = self.NIKON_CAMERA_FOLDER
            else:
                camera_folder = self.CANON_CAMERA_FOLDER

            cmd = [
                'gphoto2',
                '--force-overwrite',
                '--folder', camera_folder,
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

    def unlock(self, path):
        """
        Unlock the UI, else the camera says "BUSY" when I press any button
        """
        cmd = ['gphoto2', '--summary']
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode != 0:
            self.app.start_response('400 Bad Request', [])
            return [proc.stdout]
        #
        headers = [
            ('Content-Type', 'text/plain'),
            ]
        self.app.start_response('200 OK', headers)
        return [proc.stdout]
