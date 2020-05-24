from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.properties import NumericProperty, ReferenceListProperty
from astro.uix import MyScreen
from astro.error import MessageBox

Builder.load_file(resource_find('astro/rotationscreen.kv'))

class RotationScreen(MyScreen):
    # the rotation center
    Ox = NumericProperty(0)
    Oy = NumericProperty(0)
    O = ReferenceListProperty(Ox, Oy)

    def __init__(self, *args, **kwargs):
        super(RotationScreen, self).__init__(*args, **kwargs)
        self.ids.sky.bind(on_touch_down=self.on_sky_touch_down)

    def autoscale(self):
        tw, th = self.ids.sky.texture.size
        scale_x = self.width / float(tw)
        scale_y = self.height / float(th)
        self.ids.scatter.scale = min(scale_x, scale_y)
        self.ids.scatter.pos = (0, 0)

    def on_sky_touch_down(self, img, touch):
        self.O = touch.pos
