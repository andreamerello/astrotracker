import re
from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.properties import (NumericProperty, ReferenceListProperty, StringProperty,
                             ObjectProperty, ConfigParserProperty)
from kivy.vector import Vector
from astro.uix import MyScreen
from astro.error import MessageBox

Builder.load_file(resource_find('astro/rotationscreen.kv'))

class RotationScreen(MyScreen):
    LAST_IMAGE_REGEXP = re.compile(r'IMG_([0-9]+).JPG')

    app = ObjectProperty()
    tool = StringProperty('pan')
    last_image = ConfigParserProperty('', 'tracker', 'last_image', 'app')

    # North Pole
    NPx = NumericProperty(0)
    NPy = NumericProperty(0)
    NP = ReferenceListProperty(NPx, NPy)
    sample_radius = NumericProperty(500)

    def __init__(self, *args, **kwargs):
        super(RotationScreen, self).__init__(*args, **kwargs)
        self.ids.sky.bind(on_touch_down=self.on_sky_touch_down)
        self.ids.sky.bind(on_touch_move=self.on_sky_touch_move)
        self._load_np()

    def last_image_inc(self, step=1):
        m = self.LAST_IMAGE_REGEXP.match(self.last_image)
        if m:
            n = int(m.group(1))
            n += step
            self.last_image = 'IMG_%d.JPG' % n

    def load_image(self):
        imgfile = self.app.image_storage.join(self.last_image)
        if not imgfile.exists():
            data = self._fetch_image_from_server()
            imgfile.write(data, 'wb')
        self.ids.sky.source = str(imgfile)
        self._load_np()

    def _fetch_image_from_server(self):
        name, host, port = self.app.get_active_server()
        url = 'http://%s:%s/camera/picture/%s' % (host, port, self.last_image)
        resp = self.app.requests.get(url, timeout=120)
        assert resp.status_code == 200
        return resp.content

    def autoscale(self):
        if self.ids.sky.texture is None:
            return
        tw, th = self.ids.sky.texture.size
        scale_x = self.width / float(tw)
        scale_y = self.height / float(th)
        self.ids.scatter.scale = min(scale_x, scale_y)
        self.ids.scatter.pos = (0, 0)

    def _load_np(self):
        if self.ids.sky.texture is None:
            return
        sx, sy = self.app.load_north_pole() # coordinates in the 0-1.0 range
        # transform into "pixel" coordinates
        x = self.ids.sky.width * sx
        y = self.ids.sky.height * sy
        self.NP = (x, y)

    def _save_np(self):
        if self.ids.sky.texture is None:
            return
        sx = self.NPx / float(self.ids.sky.width)
        sy = self.NPy / float(self.ids.sky.height)
        self.app.save_north_pole((sx, sy))

    def on_NP(self, instance, value):
        self._save_np()

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
            self.NP = touch.pos
        else:
            # make sure NOT so save self.NP, else we save a *reference* to NPx
            # and NPy, not a copy
            self._old_NP = self.NPx, self.NPy
            self._movement_origin = touch.pos

    def on_tool_set_center_move(self, touch):
        if touch.grab_list:
            # someone else grabbed this movement, probably the slider. Ignore
            return
        mox, moy = self._movement_origin
        dx = touch.x - mox
        dy = touch.y - moy
        npx, npy = self._old_NP
        self.NP = npx+dx, npy+dy

    # ===============
    # set_radius tool

    def on_tool_set_radius_touch(self, touch):
        distance = Vector(self.NP).distance(touch.pos)
        self.sample_radius = distance

    def on_tool_set_radius_move(self, touch):
        if touch.grab_list:
            # someone else grabbed this movement, probably the slider. Ignore
            return
        self.on_tool_set_radius_touch(touch)
