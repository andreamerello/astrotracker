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
    texture = Texture.create(size=(width, height))
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

    def run(self):
        CHUNK_SIZE = 1024
        W, H, fps = 320, 240, 10
        ## W, H, fps = 640, 480,  5
        ## W, H, fps = 2592, 1944, 1

        #W, H = raw_resolution(W, H) # XXX
        path = 'camera?w=%s&h=%s&fps=%s' % (W, H, fps)
        FRAME_SIZE = W*H # XXX: "raw_resolution"?

        Logger.info('RemoteCamera: thread started')
        self.set_status('Connecting...')
        resp = requests.get(self.url(path), stream=True)
        #resp = requests.get(self.url('sky.mjpg'), stream=True)
        resp.raise_for_status() # XXX: handle this
        self.set_status('Connected')

        data = ''
        tstart = time.time()
        while self.running:
            data += resp.raw.read(CHUNK_SIZE)
            if len(data) > FRAME_SIZE:
                # got a full frame
                yuv_data = data[:FRAME_SIZE]
                data = data[FRAME_SIZE:]
                self.got_frame(tstart)
                self.set_yuv(yuv_data, W, H)

            ## a = data.find('\xff\xd8') # jpg_start
            ## b = data.find('\xff\xd9') # jpg_end
            ## if a != -1 and b != -1:
            ##     # found a new frame!
            ##     jpg_data = data[a:b+2]
            ##     data = data[b+2:]
            ##     # with open('/tmp/foo%d.jpg' % self.frame_no, 'wb') as f:
            ##     #     f.write(jpg_data)

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
