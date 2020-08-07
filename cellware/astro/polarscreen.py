import io
from kivy.uix.screenmanager import Screen
from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.properties import (ObjectProperty, NumericProperty, BoundedNumericProperty,
                             ReferenceListProperty)
from kivy.uix.effectwidget import EffectWidget, AdvancedEffectBase
from kivy.graphics.texture import Texture
from astro.remotecamera import RemoteCamera
from astro.uix import MyScreen
from astro.error import MessageBox
from astro.imgfilename import ImgFileName

Builder.load_file(resource_find('astro/polarscreen.kv'))

class PolarScreen(MyScreen):
    app = ObjectProperty()
    stars_angle = NumericProperty(0)
    camera = ObjectProperty(RemoteCamera())

    # North Pole
    NPx = NumericProperty(0)
    NPy = NumericProperty(0)
    NP = ReferenceListProperty(NPx, NPy)

    def __init__(self, *args, **kwargs):
        super(PolarScreen, self).__init__(*args, **kwargs)
        self.ids.imgfilename.load_image = self.load_image
        self.NP = self.app.load_north_pole() # coordinates in the 0-1.0 range
        self.camera.bind(on_remote_camera_size=self.autoscale)

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
        scale_x = self.width / float(self.camera.img_width)
        scale_y = self.height / float(self.camera.img_height)
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
        self.camera.stop()

    def start_camera(self, recording=False):
        self.ids.imgfilename.disabled = True
        if self.ids.camera_model.picam:
            fmt = self.ids.format.text.lower()
            resolution = self.ids.resolution.text
            shutter = self.ids.shutter.text
            params = '/picamera/liveview/%s/%s/' % (fmt, resolution)
            if shutter != 'auto':
                assert shutter[-1] == '"'
                shutter = shutter[:-1]
                params += '?shutter=%s' % shutter
        else:
            fps = self.ids.fps.text
            params = '/camera/liveview/?fps=%s' % fps
        self.camera.start(params, recording)

    def status_click(self):
        box = MessageBox(title='Error',
                         message=self.camera.status,
                         description=self.camera.extra_status)
        box.open()


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
