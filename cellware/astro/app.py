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
    font_size = 15.0
    std_height = font_size * 2

    def __init__(self, argv, **kwargs):
        self.argv = argv
        super(AstroApp, self).__init__(**kwargs)

    def get_timeout(self):
        return 3

    def build_config(self, config):
        config.setdefaults('server', {
            'host': '192.168.1.3',
            'port': '8000'
        })
        config.setdefaults('tracker', {
            'NP': (0.5, 0.5)
            })

    @property
    def storage(self):
        if platform == 'android':
            path = '/sdcard'
        else:
            path = '/tmp'
        return pypath.local(path)

    def build_settings(self, settings):
        from kivy.config import Config
        settings.add_json_panel('App', self.config,
                                filename=resource_find('data/settings.json'))

    def build(self):
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

    def open_rotation(self):
        screen = RotationScreen(name='rotationscreen', app=self)
        self.manager.open(screen)

    def open_polar(self):
        polar_screen = PolarScreen(name='polarsceen')
        polar_screen.camera.app = self
        self.manager.open(polar_screen)

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
