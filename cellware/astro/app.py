#!/usr/bin/env python

import kivy
kivy.require('1.9.1')

import sys
from zipfile import ZipFile
from cStringIO import StringIO
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.utils import platform
from kivy.logger import Logger
from astro.manager import Manager
from astro.error import MyExceptionHandler, MessageBox
from astro.smart_requests import SmartRequests

GITHUB_URL = 'https://github.com/andreamerello/astrotracker/archive/master.zip'

class MainMenuScreen(Screen):
    pass

class AstroApp(App):
    font_size = 15.0
    std_height = font_size * 2

    def __init__(self, **kwargs):
        super(AstroApp, self).__init__(**kwargs)

    def get_timeout(self):
        return 3

    def build(self):
        self.exception_handler = MyExceptionHandler()
        self.requests = SmartRequests(self)
        self.manager = Manager()
        self.manager.open(MainMenuScreen())
        return self.manager

    def on_pause(self):
        return True

    def open_polar(self):
        print "TODO"

    def open_camera(self):
        print "TODO"

    def upgrade_from_github(self):
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


def main():
    AstroApp().run()
