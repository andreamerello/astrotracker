import io
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty, NumericProperty
from astro.remotecamera import RemoteCamera

class PolarScreen(Screen):
    stars_angle = NumericProperty(0)
    camera = ObjectProperty(RemoteCamera())

    ## def xxx(self):
    ##     from kivy.graphics.texture import Texture
    ##     with open('frame.yuv', 'rb') as f:
    ##         data = f.read()
    ##     data = data[::-1]
    ##     texture = Texture.create(size=(320, 240))
    ##     texture.blit_buffer(data, colorfmt='luminance', bufferfmt='ubyte')
    ##     self.camera.frame_texture = texture
