import io
from kivy.uix.screenmanager import Screen
from kivy.resources import resource_find
from kivy.lang import Builder
from kivy.properties import (ObjectProperty, NumericProperty, BoundedNumericProperty,
                             ReferenceListProperty)
from kivy.uix.effectwidget import EffectWidget, AdvancedEffectBase
from astro.remotecamera import RemoteCamera
from astro.uix import MyScreen
from astro.error import MessageBox
from astro.smart_requests import SmartRequests
from astro.error import ErrorMessage

Builder.load_file(resource_find('astro/camerascreen.kv'))

class CameraScreen(MyScreen):
    app = ObjectProperty()
    camera = ObjectProperty(RemoteCamera())

    def get_timeout(self):
        return 3

    def get_supported_iso(self):
        name, host, port = self.app.get_active_server()
        url = 'http://%s:%s/camera/get_iso' % (host, port)

        try:
            resp = self.requests.get(url, timeout=120)
        except ErrorMessage:
            resp = None
        # assert resp.status_code == 200
        if resp is None or resp.status.code != 200:
            msg = MessageBox(message="Cannot get supported ISO from camera")
            isos = [str(100 *  2**i) for i in range(9)]
        else:
            isos = resp.raw.read(1024).split[',']
        return isos

    def set_iso(self, iso):
        print "setting iso to %s" % iso
        name, host, port = self.app.get_active_server()
        url = 'http://%s:%s/camera/set_iso/?iso=%s' % (host, port, iso)
        resp = self.requests.get(url, timeout=120)
        assert resp.status_code == 200

    def set_focus(self, step):
        name, host, port = self.app.get_active_server()
        url = 'http://%s:%s/camera/set_focus/?focus=%s' % (host, port, step)
        resp = self.requests.get(url, timeout=120)
        assert resp.status_code == 200

    def shot_bulb(self, secs):
        name, host, port = self.app.get_active_server()
        url = 'http://%s:%s/camera/shot_bulb/?secs=%s' % (host, port, secs)
        resp = self.requests.get(url, timeout=120)
        assert resp.status_code == 200

    def check_bulb_busy(self):
        name, host, port = self.app.get_active_server()
        url = 'http://%s:%s/camera/check_bulb/' % (host, port, secs)
        resp = self.requests.get(url, timeout=120)
        assert resp.status_code == 200
        return False if resp.raw.read(1024) == "idle" else True

    def set_astro_settings(self):
        # set video to 25p for liveview. set shutter to 1/25
        # disable LERN and HINR
        pass

    def __init__(self, *args, **kwargs):
        super(CameraScreen, self).__init__(*args, **kwargs)
        self.requests = SmartRequests(self)
        self.ids.iso.values = self.get_supported_iso()

    def autoscale(self):
        # it's a bid bad to hardcode this value: ideally, we should wait for
        # the first frame we receive from the camera, and get tw, th from it,
        # but it's too complicate and for now we know that the size is going
        # to be this.
        tw, th = 480, 320
        scale_x = self.width / float(tw)
        scale_y = self.height / float(th)
        self.ids.scatter.scale = min(scale_x, scale_y)
        self.ids.scatter.pos = (0, 0)

    def test(self):
        from astro.remotecamera import yuv_to_texture
        with open('frame.yuv', 'rb') as f:
            data = f.read()
        texture = yuv_to_texture(data, 320, 240)
        self.camera.frame_texture = texture

    def start_camera(self, recording=False):
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
