import io
import os
import time
import threading
from urlparse import urljoin
import traceback
import datetime
import collections
import requests
from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, NumericProperty)
from kivy.logger import Logger
from kivy.clock import Clock, mainthread
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

class CameraError(Exception):
    pass

def yuv_to_texture(data, width, height):
    texture = Texture.create(size=(width, height), colorfmt='luminance')
    texture.blit_buffer(data, colorfmt='luminance', bufferfmt='ubyte')
    # it seems that the pixel sequence coming from picamera is
    # updside-down compared to the one expected by Texture. Fix it!
    texture.flip_vertical()
    return texture

class RemoteCamera(EventDispatcher):
    app = ObjectProperty()
    frame_no = NumericProperty(0)
    status = StringProperty('Stopped')
    extra_status = StringProperty('')
    fps = NumericProperty(0)
    frame_texture = ObjectProperty(None)

    # ==============================
    # Main thread
    # ==============================

    def __init__(self, **kwargs):
        self.register_event_type('on_remote_frame_size')
        super(RemoteCamera, self).__init__(**kwargs)
        self.frame_size = (0, 0)
        self.running = False

    def on_remote_frame_size(self, *args):
        pass

    def url(self, path):
        name, host, port = self.app.get_active_server()
        base = 'http://%s:%s' % (host, port)
        return urljoin(base, path)

    def start(self, path):
        if self.running:
            Logger.info('RemoteCamera: WARNING: called start(), but camera already running')
            return
        self.running = True
        self.thread = threading.Thread(target=self.run, args=(path,),
                                       name='RemoteCamera')
        self.thread.daemon = True
        self.thread.start()

    def stop(self, path=None):
        if not self.running:
            Logger.info('RemoteCamera: WARNING: called stop() but camera is not running')
            if path:
                url = self.url(os.path.join(path, 'stop'))
                requests.get(url)
            return
        self.running = False

    @mainthread
    def set_status(self, status, extra=''):
        self.status = status
        self.extra_status = extra

    @mainthread
    def set_jpg(self, jpg):
        # create a texture from the jpg data. This needs to be done in the main
        # thread, else it seems that kivy cannot display the texture, don't know
        # why.
        stream = io.BytesIO(jpg)
        img = CoreImage(stream, ext="jpg")
        if self.frame_size != img.size:
            self.frame_size = img.size
            self.dispatch('on_remote_frame_size')
        self.frame_texture = img.texture

    @mainthread
    def set_yuv(self, data, width, height):
        self.frame_texture = yuv_to_texture(data, width, height)

    # ==============================
    # RemoteCamera thread
    # ==============================

    def run(self, path):
        """
        path is relative to the remote server. E.g., '/camera/liveview/'
        """
        Logger.info('RemoteCamera: thread started')
        url = self.url(path)
        Logger.info('RemoteCamera: connecting to %s' % self.url)
        self.set_status('Connecting...')
        try:
            self._camera_loop(url)
        except CameraError as e:
            self.stop()
            self.set_status('Camera Error', str(e))
            Logger.exception('RemoteCamera: CameraError')
        except Exception as e:
            self.stop()
            self.set_status('Error', traceback.format_exc())
            Logger.exception('RemoteCamera: Error')
        else:
            self.set_status('Stopped')
            Logger.info('RemoteCamera: stop')

    def _camera_loop(self, url):
        session = requests.session()
        self.frame_no = 0
        self.frame_size = (0, 0)
        frame_times = collections.deque([time.time()], maxlen=25)
        while self.running:
            resp = session.get(url)
            if resp.status_code == 400:
                # this happens in case of gphoto-related errors
                raise CameraError(resp.text)
            resp.raise_for_status()  # treat all the other HTTP errors as exceptions
            self.set_status('Connected')
            #
            ct = resp.headers['Content-Type']
            if ct == 'image/jpeg':
                self.set_jpg(resp.content)
            elif ct == 'image/yuv':
                # NOTE: this is untested
                self.set_yuv(resp.content)
            else:
                raise ValueError('Unsupported Content-Type: %s' % ct)

            try:
                self.frame_no = int(resp.headers['X-Frame-Number'])
            except (KeyError, ValueError):
                pass

            frame_times.append(time.time())
            self.fps = len(frame_times) / (frame_times[-1] - frame_times[0])
            #Logger.info('RemoteCamera: %.2f fps' % self.fps)
            if self.fps > 100:
                # sleep a bit: for the polaris stream this is not an issue since
                # it will be at a very low fps. However, if you try to display a
                # MJPG with an unbounded framerate, if you don't put the sleep
                # you put too many tasks into kivy's @mainthread and things
                # seems to hang.
                time.sleep(0.01)
        #
        # stop the gphoto thread on the remote side
        session.get(os.path.join(url, 'stop'))
        self.set_status('Stopped')
