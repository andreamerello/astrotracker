import io
import time
import threading
from urlparse import urljoin
import traceback
import datetime
import requests
from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, NumericProperty)
from kivy.logger import Logger
from kivy.clock import Clock, mainthread
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

class CameraNotFound(Exception):
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
        self.register_event_type('on_remote_camera_size')
        super(RemoteCamera, self).__init__(**kwargs)
        self.img_width, self.img_height = 480, 320
        self.running = False

    def on_remote_camera_size(self, *args):
        pass

    def url(self, path):
        name, host, port = self.app.get_active_server()
        base = 'http://%s:%s' % (host, port)
        return urljoin(base, path)

    def start(self, params, recording=False):
        if self.running:
            Logger.info('RemoteCamera: WARNING: called start(), but camera already running')
            return
        self.running = True
        self.thread = threading.Thread(target=self.run, args=(params, recording),
                                       name='RemoteCamera')
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if not self.running:
            Logger.info('RemoteCamera: WARNING: called stop() but camera is not running')
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
        if (self.img_width != img.width) or (self.img_height != img.height):
            self.img_width = img.width
            self.img_height = img.height
            self.dispatch('on_remote_camera_size')
        self.frame_texture = img.texture

    @mainthread
    def set_yuv(self, data, width, height):
        self.frame_texture = yuv_to_texture(data, width, height)

    # ==============================
    # RemoteCamera thread
    # ==============================

    def run(self, params, recording):
        Logger.info('RemoteCamera: thread started')
        url = self.url(params)
        Logger.info('RemoteCamera: connecting to %s' % url)
        self.set_status('Connecting...')
        try:
            self._camera_loop(url, recording)
        except CameraNotFound as e:
            self.stop()
            self.set_status('No camera', str(e))
            Logger.exception('RemoteCamera: CameraNotFound')
        except Exception as e:
            self.stop()
            self.set_status('Error', traceback.format_exc())
            Logger.exception('RemoteCamera: Error')
        else:
            self.set_status('Stopped')
            Logger.info('RemoteCamera: stop')

    def _camera_loop(self, url, recording):
        resp = requests.get(url, stream=True)
        if resp.status_code == 400:
            # it's very likely that it's camera not found
            raise CameraNotFound(resp.text)
        # treat all the other HTTP errors as exceptions
        resp.raise_for_status()

        ct = resp.headers['Content-Type']
        if ct == 'video/x-raw':
            fmt = 'yuv'
            width = int(resp.headers['X-Width'])
            height = int(resp.headers['X-Height'])
            frame_size = width * height
            ext = '.%dx%d.yuv' % (width, height)
        elif ct == 'video/x-motion-jpeg':
            fmt = 'jpg'
            width = 0
            height = 0
            frame_size = 0
            ext = '.mjpg'
        else:
            raise ValueError('Unsupported Content-Type: %s' % ct)

        if recording:
            self.set_status('Recording')
            now = datetime.datetime.now()
            fname = self.app.storage.join(now.strftime('polaris %Y-%m-%d %H.%M') + ext)
            Logger.info('RemoteCamera: recording to %s' % fname)
            outfile = fname.open('wb')
        else:
            self.set_status('Playing')
            outfile = None

        data = ''
        self.frame_no = 0
        tstart = time.time()
        while self.running:
            chunk = resp.raw.read(1024)
            if outfile:
                outfile.write(chunk)
            data += chunk
            if fmt == 'yuv' and len(data) > frame_size:
                # got a full frame
                yuv_data = data[:frame_size]
                data = data[frame_size:]
                self.got_frame(tstart)
                self.set_yuv(yuv_data, width, height)

            elif fmt == 'jpg':
                a = data.find('\xff\xd8') # jpg_start
                b = data.find('\xff\xd9') # jpg_end
                if a != -1 and b != -1:
                    # found a new frame!
                    jpg_data = data[a:b+2]
                    data = data[b+2:]
                    self.got_frame(tstart)
                    self.set_jpg(jpg_data)

        if outfile:
            outfile.close()

    def got_frame(self, tstart):
        self.frame_no += 1
        t = time.time()
        self.fps = self.frame_no / (t-tstart)
        Logger.info('RemoteCamera: %.2f fps' % self.fps)
        # sleep a bit: for the polaris stream this is not an issue since
        # it will be at a very low fps. However, if you try to display a
        # MJPG with an unbounded framerate, if you don't put the sleep
        # you put too many tasks into kivy's @mainthread and things
        # seems to hang.
        time.sleep(0.01)
