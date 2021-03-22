import io
import math
from collections import OrderedDict
from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.properties import (ObjectProperty, NumericProperty, BoundedNumericProperty,
                             ReferenceListProperty, StringProperty, AliasProperty)
from kivy.uix.effectwidget import EffectWidget, AdvancedEffectBase
from kivy.event import EventDispatcher
from kivy.graphics.texture import Texture
from astro.remotecamera import RemoteCamera
from astro.uix import MyScreen
from astro.error import MessageBox
from astro.imgfilename import ImgFileName

Builder.load_file(resource_find('astro/polarscreen.kv'))

def LST(longitude, dt):
    """
    Compute the Local Siderial Time.

    longitude: the longitude of the observer, in degrees
    dt: datetime, the universal time of the observer

    Return: the LST in degrees
    """
    # http://www.stargazing.net/kepler/altaz.html
    # compute the number of days since J2000.0
    delta = dt - datetime(2000, 1, 1, 12, 0, 0)
    days = delta.total_seconds() / 86400.0
    ut = dt.hour + (dt.minute/60.0) + (dt.second/3600.0)
    return (100.46 + 0.985647 * days + longitude + 15*ut) % 360



class PolarSettings(EventDispatcher):
    location = StringProperty('')
    latitude = NumericProperty(0)  # degrees
    longitude = NumericProperty(0) # degrees
    lens = StringProperty('Canon-75mm')
    extra_stars_angle = NumericProperty(0)

    # XXX: would be nice to avoid hardcoding locations here
    _locations = OrderedDict([
        ('Mele',          (44.44488007399028,  8.747941571537185)),
        ('Genova',        (44.415511121949734, 8.886021164909707)),
        ('Valtournenche', (45.885880860274405, 7.624707693459453)),
        ('Argentera',     (44.39671224702886,  6.937148403030893)),
        ])

    def get_all_locations(self):
        return tuple(self._locations.keys())
    all_locations = AliasProperty(get_all_locations, None)

    def __init__(self, *args, **kwargs):
        super(PolarSettings, self).__init__(*args, **kwargs)
        self.location = 'Mele' # force update

    def on_location(self, _, value):
        lat, lon = self._locations.get(value, (0, 0))
        self.latitude = lat
        self.longitude = lon

    def get_stars_angle(self):
        # XXX: ideally, this should be automatically updated after a while,
        # keeping sync with utcnow
        lst = LST(self.longitude, datetime.utcnow())
        return lst + self.extra_stars_angle
    stars_angle = AliasProperty(get_stars_angle, None,
                                bind=['extra_stars_angle', 'longitude']) # XXX time?

    def get_lens_filename(self):
        return 'lens/%s.png' % self.lens
    lens_filename = AliasProperty(get_lens_filename, None, bind=['lens'])

class PolarSettingsScreen(MyScreen):
    settings = ObjectProperty(PolarSettings())


class PolarScreen(MyScreen):
    app = ObjectProperty()
    settings = PolarSettings()
    camera = ObjectProperty(RemoteCamera())

    # North Pole
    NPx = NumericProperty(0)
    NPy = NumericProperty(0)
    NP = ReferenceListProperty(NPx, NPy)

    def __init__(self, *args, **kwargs):
        super(PolarScreen, self).__init__(*args, **kwargs)
        self.ids.imgfilename.load_image = self.load_image
        self.NP = self.app.load_north_pole() # coordinates in the 0-1.0 range
        self.camera.bind(on_remote_frame_size=self.autoscale)

    def open_settings(self):
        screen = PolarSettingsScreen(name='polarsettings', settings=self.settings)
        self.app.manager.open(screen)

    def load_image(self):
        imgfile = self.app.image_storage.join(self.ids.imgfilename.last_image)
        if not imgfile.exists():
            data = self._fetch_image_from_server()
            imgfile.write(data, 'wb')
        else:
            data = imgfile.read()
        self.camera.set_jpg(data)

    def _fetch_image_from_server(self):
        name, host, port = self.app.get_active_server()
        url = 'http://%s:%s/camera/picture/%s' % (host, port, self.ids.imgfilename.last_image)
        resp = self.app.requests.get(url, timeout=120)
        assert resp.status_code == 200
        return resp.content

    def autoscale(self, *args):
        w, h = self.camera.frame_size
        scale_x = self.width / float(w)
        scale_y = self.height / float(h)
        self.ids.scatter.scale = min(scale_x, scale_y)
        self.ids.scatter.pos = (0, 0)

    def test(self):
        from astro.remotecamera import yuv_to_texture
        with open('frame.yuv', 'rb') as f:
            data = f.read()
        texture = yuv_to_texture(data, 320, 240)
        self.camera.frame_texture = texture

    def stop_camera(self):
        self.ids.imgfilename.disabled = False
        self.camera.stop('/camera/liveview/')

    def start_camera(self):
        self.ids.imgfilename.disabled = True
        if False and self.ids.camera_model.picam:
            # picamera code commented out for now
            fmt = self.ids.format.text.lower()
            resolution = self.ids.resolution.text
            shutter = self.ids.shutter.text
            path = '/picamera/liveview/%s/%s/' % (fmt, resolution)
            if shutter != 'auto':
                assert shutter[-1] == '"'
                shutter = shutter[:-1]
                path += '?shutter=%s' % shutter
        else:
            path = '/camera/liveview/'
        self.camera.start(path)

    def status_click(self):
        box = MessageBox(title='Error',
                         message=self.camera.status,
                         description=self.camera.extra_status)
        box.open()

    def on_pre_leave(self):
        if self.camera.running:
            self.stop_camera()

effect_string = '''
// the uniforms are in the range 0.0-1.0
uniform float black;
uniform float white;

float clip(float x)
{
    if (x <= black) return 0.0;
    if (x >= white) return 1.0;
    return x * (white-black);
}

vec4 effect(vec4 color, sampler2D texture, vec2 tex_coords, vec2 coords)
{
    float red = clip(color.x);
    float green = clip(color.y);
    float blue = clip(color.z);
    return vec4(red, green, blue, color.w);
}
'''

class ColorClippingEffect(AdvancedEffectBase):
    def __init__(self, *args, **kwargs):
        super(ColorClippingEffect, self).__init__(*args, **kwargs)
        self.glsl = effect_string
        self.uniforms = {'black': 0.0, 'white': 1.0}


class ColorClippingWidget(EffectWidget):
    # the user properties are in the range 0-255
    black = BoundedNumericProperty(0, min=0, max=255, errorvalue=0)
    white = BoundedNumericProperty(255, min=0, max=255, errorvalue=255)

    def __init__(self, *args, **kwargs):
        super(ColorClippingWidget, self).__init__(*args, **kwargs)
        self.clip_effect = ColorClippingEffect()
        self.effects = [self.clip_effect]

    def on_black(self, *args):
        self.clip_effect.uniforms['black'] = self.black/255.0

    def on_white(self, *args):
        self.clip_effect.uniforms['white'] = self.white/255.0
