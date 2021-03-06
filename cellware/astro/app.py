#!/usr/bin/env python

import kivy
kivy.require('1.9.1')

import sys
from zipfile import ZipFile
from cStringIO import StringIO
from kivy.app import App
from kivy.resources import resource_find
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.utils import platform
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.metrics import sp, Metrics
import pypath
import astro.uix
from astro import iconfonts
from astro.rotationscreen import RotationScreen
from astro.polarscreen import PolarScreen
from astro.manager import Manager
from astro.error import MyExceptionHandler, MessageBox, ErrorMessage
from astro.smart_requests import SmartRequests
from astro.uix import MyScreen

GITHUB_URL = 'https://github.com/andreamerello/astrotracker/archive/master.zip'

class MainMenuScreen(MyScreen):
    pass

class AstroApp(App):
    font_size = sp(15.0)
    std_height = font_size * 2

    def __init__(self, argv, **kwargs):
        self.argv = argv
        super(AstroApp, self).__init__(**kwargs)

    def get_timeout(self):
        return 3

    def build_config(self, config):
        config.setdefaults('server', {
            'active': '1',
            })
        config.setdefaults('server1', {
            'name': 'default',
            'host': '192.168.1.3',
            'port': '8000',
            })
        config.setdefaults('server2', {
            'name': 'alternative',
            'host': '192.168.43.81',
            'port': '8000',
            })
        config.setdefaults('tracker', {
            'NP': (0.5, 0.5),
            'last_image': 'IMG_1000.JPG',
            })

    @property
    def storage(self):
        if platform == 'android':
            path = '/sdcard'
        else:
            path = '/tmp'
        return pypath.local(path)

    @property
    def image_storage(self):
        return self.storage.join('astropi').ensure(dir=True)

    def build_settings(self, settings):
        from kivy.config import Config
        settings.add_json_panel('App', self.config,
                                filename=resource_find('data/settings.json'))

    def get_active_server(self):
        active = self.config.get('server', 'active')
        section = 'server' + active
        name = self.config.get(section, 'name')
        host = self.config.get(section, 'host')
        port = self.config.get(section, 'port')
        return name, host, port

    def log_metrics(self):
        Logger.info('metrics: Window.size is %sx%s' % Window.size)
        Logger.info('metrics: dpi = %s' % Metrics.dpi)
        Logger.info('metrics: density = %s' % Metrics.density)
        Logger.info('metrics: fontscale = %s' % Metrics.fontscale)

    def build(self):
        self.log_metrics()
        Window.bind(on_keyboard=self.on_keyboard)
        self.exception_handler = MyExceptionHandler()
        self.requests = SmartRequests(self)
        self.manager = Manager()
        self.manager.open(MainMenuScreen())
        if '--rotation' in self.argv:
            self.open_rotation()
        elif '--polar' in self.argv:
            self.open_polar()
            ## self.manager.current_view.test()
        return self.manager

    def on_pause(self):
        return True

    def on_keyboard(self, window, keycode, scancode, text, modifiers):
        if keycode == 27: # ESC
            return self.root.go_back()

    def load_north_pole(self):
        try:
            src = self.config.get('tracker', 'NP')
            np = eval(src)
        except Exception as e:
            msg = MessageBox(message="Error when loading the North Pole location",
                             description='%s\n%s' % (src, str(e)))
            Clock.schedule_once(msg.open, 0)
            return (0, 0)
        else:
            return np

    def save_north_pole(self, p):
        self.config.set('tracker', 'NP', str(p))
        self.config.write()

    def open_rotation(self):
        screen = RotationScreen(name='rotationscreen', app=self)
        self.manager.open(screen)

    def open_polar(self):
        polar_screen = PolarScreen(name='polarsceen', app=self)
        polar_screen.camera.app = self
        self.manager.open(polar_screen)
        #polar_screen.open_settings()

    def unlock_camera(self):
        name, host, port = self.get_active_server()
        url = 'http://%s:%s/camera/unlock/' % (host, port)
        resp = self.requests.get(url, timeout=120)
        assert resp.status_code == 200

    def open_camera(self):
        print "TODO"

    def upgrade_from_github(self):
        raise ErrorMessage("FIX ME")
        if platform == 'android':
            dest = '/sdcard/kivy'
        else:
            dest = '/tmp/kivy'
        Logger.info('downloading zip from github')
        resp = self.requests.get(GITHUB_URL)
        Logger.info('unzipping to %s' % dest)
        f = StringIO(resp.content)
        zipf = ZipFile(f)
        zipf.extractall(dest)
        Logger.info('Upgrade done')
        box = MessageBox(title='Upgrade',
                         message='Upgrade completed',
                         description='Restart the application')
        box.open()


def main(argv):
    iconfonts.init()
    AstroApp(argv).run()
