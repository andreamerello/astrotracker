from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import (NumericProperty, ReferenceListProperty, StringProperty,
                             ObjectProperty)
from kivy.vector import Vector
from astro.uix import MyScreen
from astro.error import MessageBox

Builder.load_file(resource_find('astro/rotationscreen.kv'))

class RotationScreen(MyScreen):
    app = ObjectProperty()
    tool = StringProperty('pan')
    # the rotation center
    Ox = NumericProperty(0)
    Oy = NumericProperty(0)
    O = ReferenceListProperty(Ox, Oy)

    sample_radius = NumericProperty(500)

    def __init__(self, *args, **kwargs):
        super(RotationScreen, self).__init__(*args, **kwargs)
        self.ids.sky.bind(on_touch_down=self.on_sky_touch_down)
        self.ids.sky.bind(on_touch_move=self.on_sky_touch_move)
        self._load_center()

    def autoscale(self):
        tw, th = self.ids.sky.texture.size
        scale_x = self.width / float(tw)
        scale_y = self.height / float(th)
        self.ids.scatter.scale = min(scale_x, scale_y)
        self.ids.scatter.pos = (0, 0)

    def _load_center(self):
        # sp is expressed as coordinates in the 0-1.0 range
        try:
            src = self.app.config.get('tracker', 'center')
            sp = eval(src)
            sx, sy = sp
        except Exception as e:
            self.O = (0, 0)
            msg = MessageBox(message="Error when loading the center from the settings",
                             description='%s\n%s' % (src, str(e)))
            Clock.schedule_once(msg.open, 0)
            return

        # transform into "pixel" coordinates
        x = int(self.ids.sky.width * sx)
        y = int(self.ids.sky.height * sy)
        self.O = (x, y)

    def save(self):
        sx = self.Ox / float(self.ids.sky.width)
        sy = self.Oy / float(self.ids.sky.height)
        self.app.config.set('tracker', 'center', str([sx, sy]))
        self.app.config.write()

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
