import io
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, NumericProperty
from astro.remotecamera import RemoteCamera

class PolarScreen(Screen):
    stars_angle = NumericProperty(0)
    camera = ObjectProperty(RemoteCamera())

    # def fakeimg(self):
    #     with open("fakeimg.png", "rb") as f:
    #         stream = io.BytesIO(f.read())
    #         img = CoreImage(stream, ext="png")
    #         self.piframe_texture = img.texture
