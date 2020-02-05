import io
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, NumericProperty
from astro.remotecamera import RemoteCamera
from astro.uix import MyScreen

class PolarScreen(MyScreen):
    stars_angle = NumericProperty(0)
    camera = ObjectProperty(RemoteCamera())

    def test(self):
        from astro.remotecamera import yuv_to_texture
        with open('frame.yuv', 'rb') as f:
            data = f.read()
        texture = yuv_to_texture(data, 320, 240)
        self.camera.frame_texture = texture

    def start_camera(self, recording=False):
        fmt = self.ids.format.text.lower()
        resolution = self.ids.resolution.text
        shutter = self.ids.shutter.text
        params = '/camera/%s/%s/' % (fmt, resolution)
        if shutter != 'auto':
            assert shutter[-1] == '"'
            shutter = shutter[:-1]
            params += '?shutter=%s' % shutter
        self.camera.start(params, recording)
