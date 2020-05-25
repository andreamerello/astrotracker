from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.properties import NumericProperty, ReferenceListProperty, StringProperty
from kivy.vector import Vector
from astro.uix import MyScreen
from astro.error import MessageBox

Builder.load_file(resource_find('astro/rotationscreen.kv'))

class RotationScreen(MyScreen):
    tool = StringProperty('pan')
    # the rotation center
    Ox = NumericProperty(3000)
    Oy = NumericProperty(2000)
    O = ReferenceListProperty(Ox, Oy)

    sample_radius = NumericProperty(500)

    def __init__(self, *args, **kwargs):
        super(RotationScreen, self).__init__(*args, **kwargs)
        self.ids.sky.bind(on_touch_down=self.on_sky_touch_down)
        self.ids.sky.bind(on_touch_move=self.on_sky_touch_move)

    def autoscale(self):
        tw, th = self.ids.sky.texture.size
        scale_x = self.width / float(tw)
        scale_y = self.height / float(th)
        self.ids.scatter.scale = min(scale_x, scale_y)
        self.ids.scatter.pos = (0, 0)

    def on_sky_touch_down(self, img, touch):
        meth = getattr(self, 'on_tool_%s_touch' % self.tool, None)
        if meth:
            return meth(touch)

    def on_sky_touch_move(self, img, touch):
        meth = getattr(self, 'on_tool_%s_move' % self.tool, None)
        if meth:
            return meth(touch)

    # ===============
    # set_center tool

    def on_tool_set_center_touch(self, touch):
        if touch.is_double_tap:
            self.O = touch.pos
        else:
            # make sure NOT so save self.O, else we save a *reference* to Ox
            # and Oy, not a copy
            self._old_O = self.Ox, self.Oy
            self._movement_origin = touch.pos

    def on_tool_set_center_move(self, touch):
        if touch.grab_list:
            # someone else grabbed this movement, probably the slider. Ignore
            return
        mox, moy = self._movement_origin
        dx = touch.x - mox
        dy = touch.y - moy
        ox, oy = self._old_O
        self.O = ox+dx, oy+dy

    # ===============
    # set_radius tool

    def on_tool_set_radius_touch(self, touch):
        distance = Vector(self.O).distance(touch.pos)
        self.sample_radius = distance

    def on_tool_set_radius_move(self, touch):
        if touch.grab_list:
            # someone else grabbed this movement, probably the slider. Ignore
            return
        self.on_tool_set_radius_touch(touch)
