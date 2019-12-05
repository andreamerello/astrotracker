import io
from kivy.uix.screenmanager import Screen
from kivy.core.image import Image as CoreImage
from kivy.properties import ObjectProperty, NumericProperty

class PolarScreen(Screen):
    piframe_texture = ObjectProperty(None)
    stars_angle = NumericProperty(0)

    def fakeimg(self):
        with open("fakeimg.png", "rb") as f:
            stream = io.BytesIO(f.read())
            img = CoreImage(stream, ext="png")
            self.piframe_texture = img.texture
