import io
from kivy.uix.screenmanager import Screen
from kivy.core.image import Image as CoreImage
from kivy.properties import ObjectProperty, NumericProperty
from astro.remotecamera import RemoteCamera



class PolarScreen(Screen):
    piframe_texture = ObjectProperty(None)
    stars_angle = NumericProperty(0)
    camera = RemoteCamera(url='http://localhost:8000/foo.mjpg')

    def fakeimg(self):
        with open("fakeimg.png", "rb") as f:
            stream = io.BytesIO(f.read())
            img = CoreImage(stream, ext="png")
            self.piframe_texture = img.texture
