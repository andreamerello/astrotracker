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
