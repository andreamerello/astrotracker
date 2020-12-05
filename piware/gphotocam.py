import os
import time
import subprocess
import collections
from pathlib import Path
import threading
from utils import terminate, iter_mjpg

try:
    import gphoto2 as gp
except ImportError:
    print('WARNING: cannot import gphoto2, using a fake module')
    class gp:
        class GPhoto2Error(Exception):
            pass

class LiveView:
    """
    Abstract class
    """

    state = None # 'STARTED', 'STOPPED', ...

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def get_latest_frame(self):
        """
        Return: (frame_no, bytes_data)
        """
        raise NotImplementedError


class LibGphotoLiveview(LiveView):
    """
    An implementation of LiveView which grabs the preview frames using libgphoto
    """

    TIMEOUT = 10.0 # seconds

    def __init__(self):
        self._camera = None
        self._last_frame_query = None
        self._frame_no = None
        self._timeout_thread = None
        self._kill_timeout_thread = threading.Event()

    @property
    def state(self):
        if self._timeout_thread:
            return 'STARTED'
        else:
            return 'STOPPED'

    def log(self, *args):
        print('[LiveView]', *args)

    def start(self):
        self.log('Starting')
        assert self.state == 'STOPPED'
        self.init_camera()
        self.set_config('output', 'TFT + PC')
        self._last_frame_query = time.time()
        self._frame_no = -1
        self._start_timeout_thread()

    def stop(self):
        if self.state == 'STOPPED':
            return
        self.log('Stopping...')
        if self._camera:
            try:
                self.set_config('output', 'TFT')
                self._camera.exit()
            except gp.GPhoto2Error as e:
                self.log('Error when shutting down the camera', e)
            self._camera = None
        self._stop_timeout_thread()

    def init_camera(self):
        self._camera = gp.Camera()
        self._camera.init()

    def set_config(self, name, value):
        self.log('set_config: %s = %s' % (name, value))
        config = self._camera.get_config()
        widget = config.get_child_by_name(name)
        widget.set_value(value)
        self._camera.set_config(config)

    def get_latest_frame(self):
        self._last_frame_query = time.time()
        capture = self._camera.capture_preview()
        filedata = capture.get_data_and_size()
        self._frame_no += 1
        return (self._frame_no, memoryview(filedata).tobytes())

    def _start_timeout_thread(self):
        def run():
            self.log('Timeout thread started')
            while True:
                #self.log('The timeout thread is alive')
                elapsed = time.time() - self._last_frame_query
                if elapsed > self.TIMEOUT:
                    self.log('Timeout! Stopping camera')
                    self.stop()
                should_be_killed = self._kill_timeout_thread.wait(timeout=1.0)
                if should_be_killed:
                    break
            self.log('Exiting timeout thread')
        #
        self._timeout_thread = threading.Thread(target=run, name='timeout thread')
        self._timeout_thread.daemon = True
        self._timeout_thread.start()

    def _stop_timeout_thread(self):
        self._kill_timeout_thread.set() # send the kill event
        self._timeout_thread = None # state == 'STOPPED'


class FakeLiveView:

    def __init__(self, videofile):
        self.videofile = videofile
        self.i = -1
        self.f = None
        self.my_iter = None

    @property
    def state(self):
        if self.my_iter:
            return 'STARTED'
        else:
            return 'STOPPED'

    def start(self):
        self.f = open(self.videofile, 'rb')
        self.my_iter = iter_mjpg(self.f)

    def stop(self):
        self.my_iter.close()
        self.f.close()
        self.my_iter = None
        self.f = None
        self.i = -1

    def get_latest_frame(self):
        """
        Return: (frame_no, bytes_data)
        """
        frame_bytes = next(self.my_iter)
        self.i += 1
        return (self.i, frame_bytes)



class GPhotoCamera:

    # XXX find this programmatically:
    #    gphoto2 --list-folders
    CANON_CAMERA_FOLDER = '/store_00020001/DCIM/100CANON/'
    NIKON_CAMERA_FOLDER = '/store_00010001/DCIM/100D5300/'
    CAPTURE_DIR = Path('/tmp/pictures')

    def __init__(self, app, fake_camera_file):
        self.app = app
        self.CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        if fake_camera_file:
            self._liveview = FakeLiveView(fake_camera_file)
        else:
            self._liveview = LibGphotoLiveview()

    def liveview(self, path):
        if path == '/camera/liveview/':
            return self.liveview_frame()
        elif path == '/camera/liveview/stop/':
            return self.liveview_stop()
        else:
            self.app.start_response('404 Not Found', [])
            return [('Path not found: %s' % path).encode('utf-8')]

    def liveview_stop(self):
        self._liveview.stop()
        self.app.start_response('200 OK', [])
        return [b'OK']

    def liveview_frame(self):
        try:
            if self._liveview.state == 'STOPPED':
                self._liveview.start()
            assert self._liveview.state == 'STARTED'
            #
            n, frame_bytes = self._liveview.get_latest_frame()
            headers = [
                ('Content-Type', 'image/jpeg'),
                ('X-Frame-Number', str(n)),
            ]
            self.app.start_response('200 OK', headers)
            return [frame_bytes]

        except gp.GPhoto2Error as e:
            self._liveview.stop()
            self.app.start_response('400 Bad Request', [])
            return [str(e).encode('utf-8')]

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
