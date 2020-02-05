import io
import time
import threading
from urlparse import urljoin
import requests
from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, NumericProperty)
from kivy.logger import Logger
from kivy.clock import Clock, mainthread
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

def yuv_to_texture(data, width, height):
    # it seems that the pixel sequence coming from picamera is
    # updside-down compared to the one expected by Texture. Fix it!
    data = data[::-1]
    texture = Texture.create(size=(width, height), colorfmt='luminance')
    texture.blit_buffer(data, colorfmt='luminance', bufferfmt='ubyte')
    return texture

class RemoteCamera(EventDispatcher):
    app = ObjectProperty()
    frame_no = NumericProperty(0)
    status = StringProperty('Stopped')
    frame_texture = ObjectProperty(None)

    # ==============================
    # Main thread
    # ==============================

    def __init__(self, **kwargs):
        super(RemoteCamera, self).__init__(**kwargs)
        self.running = False

    def url(self, path):
        host = self.app.config.get('server', 'host')
        port = self.app.config.get('server', 'port')
        base = 'http://%s:%s' % (host, port)
        return urljoin(base, path)

    def start(self):
        if self.running:
            Logger.info('RemoteCamera: WARNING: called start(), but camera already running')
            return
        self.running = True
        self.thread = threading.Thread(target=self.run, name='RemoteCamera')
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if not self.running:
            Logger.info('RemoteCamera: WARNING: called stop() but camera is not running')
            return
        self.running = False

    @mainthread
    def set_status(self, status):
        self.status = status

    @mainthread
    def set_jpg(self, jpg):
        # create a texture from the jpg data. This needs to be done in the main
        # thread, else it seems that kivy cannot display the texture, don't know
        # why.
        stream = io.BytesIO(jpg)
        img = CoreImage(stream, ext="jpg")
        self.frame_texture = img.texture

    @mainthread
    def set_yuv(self, data, width, height):
        self.frame_texture = yuv_to_texture(data, width, height)

    # ==============================
    # RemoteCamera thread
    # ==============================

    def get_url(self):
        # XXX: investigate resolution 1296x972: this is binned, so we might
        # capture more light, but it seems we can't go slower than 1fps
        path = 'camera/yuv/?w=320&h=240&fps=10'
        #path = 'camera/yuv/?shutter=1'
        #path = 'camera/jpg/?shutter=1'
        #path = 'camera/jpg/?w=320&h=240&fps=10'
        #path = 'camera/yuv/?w=1296&h=972&fps=1'
        return self.url(path)

    def run(self):
        Logger.info('RemoteCamera: thread started')
        self.set_status('Connecting...')
        url = self.get_url()
        resp = requests.get(url, stream=True)
        resp.raise_for_status() # XXX: handle this

        ct = resp.headers['Content-Type']
        if ct == 'video/x-raw':
            fmt = 'yuv'
            width = int(resp.headers['X-Width'])
            height = int(resp.headers['X-Height'])
            frame_size = width * height
        elif ct == 'video/x-motion-jpeg':
            fmt = 'jpg'
            width = 0
            height = 0
            frame_size = 0
        else:
            raise ValueError('Unsupported Content-Type: %s' % ct)

        self.set_status('Connected')

        data = ''
        tstart = time.time()
        while self.running:
            data += resp.raw.read(1024)
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

        self.set_status('Stopped')
        Logger.info('RemoteCamera: stop')

    def got_frame(self, tstart):
        self.frame_no += 1
        t = time.time()
        fps = self.frame_no / (t-tstart)
        Logger.info('RemoteCamera: %.2f fps' % fps)
        # sleep a bit: for the polaris stream this is not an issue since
        # it will be at a very low fps. However, if you try to display a
        # MJPG with an unbounded framerate, if you don't put the sleep
        # you put too many tasks into kivy's @mainthread and things
        # seems to hang.
        time.sleep(0.01)
