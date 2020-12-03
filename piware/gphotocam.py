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



class GPhotoLiveView:

    FAKE_CAPTURE = None
    #FAKE_CAPTURE = 'gphoto-capture-20s.mjpg'

    def __init__(self):
        self.status = 'STOPPED'
        self.thread = None
        self.last_frame = None
        self.n_frame = -1

    def start(self):
        assert self.status == 'STOPPED' # XXX todo
        self.status = 'STARTING'
        self.thread = threading.Thread(target=self.run, name='GPhotoLiveView.run')
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.should_stop = True

    def log(self, *args):
        print('[GPhotoLiveView]', *args)

    def run(self):
        self.status = 'STARTING'
        self.should_stop = False
        if self.FAKE_CAPTURE:
            cmd = ['python3',
                   'fake-gphoto-capture.py',
                   self.FAKE_CAPTURE
                   ]
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
            self.status = 'ERROR'
            self.error = stderr + out0
            self.running = False
            return
        #
        # if we are here, gphoto is streaming correctly, let's read the frames
        self.status = 'STREAMING'
        try:
            # XXX: kill gphoto if nobody has asked for a frame in the last X seconds
            self.n_frame = 0
            for frame in iter_mjpg(p.stdout, out0+out1):
                self.last_frame = frame
                self.n_frame += 1
                if self.n_frame % 10 == 0:
                    self.log('got frame', self.n_frame)
                if self.should_stop:
                    self.log('should_stop received, exiting')
                    return
        finally:
            self.log('terminating process')
            terminate(p)
            if not self.FAKE_CAPTURE:
                # make sure to unlock the camera at the end
                os.system('gphoto2 --set-config output=TFT')
            self.status = 'STOPPED'


class GPhotoCamera:

    # XXX find this programmatically:
    #    gphoto2 --list-folders
    CANON_CAMERA_FOLDER = '/store_00020001/DCIM/100CANON/'
    NIKON_CAMERA_FOLDER = '/store_00010001/DCIM/100D5300/'
    CAPTURE_DIR = Path('/tmp/pictures')

    def __init__(self, app, videofile):
        self.app = app
        self.videofile = videofile
        self.CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        self.liveview_thread = GPhotoLiveView()

    def liveview(self, path):
        if self.liveview_thread.status == 'STOPPED':
            print('Starting liveview')
            self.liveview_thread.start()
            t = time.time()
            while self.liveview_thread.status == 'STARTING':
                elapsed = time.time() - t
                if elapsed > 5.0:
                    print('liveview did not start :(')
                    return self.error(b'liveview did not start')
                print('    waiting...')
                time.sleep(0.1)

        if self.liveview_thread.status == 'ERROR':
            self.app.start_response('400 Bad Request', [])
            return [self.liveview_thread.error]

        if self.liveview_thread.status == 'STREAMING':
            # return the last frame
            headers = [
                ('Content-Type', 'image/jpeg'),
                ('X-Frame-Number', str(self.liveview_thread.n_frame)),
            ]
            self.app.start_response('200 OK', headers)
            return [self.liveview_thread.last_frame]

        # if we are here, we are in an unexpected state
        return self.error('Unknown thread state: %s' % self.liveview_thread.status)

    def error(self, message):
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
