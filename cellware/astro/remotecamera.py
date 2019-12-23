import time
import threading
import requests
from kivy.event import EventDispatcher
from kivy.properties import (StringProperty, ObjectProperty, NumericProperty)
from kivy.logger import Logger
from kivy.clock import Clock, mainthread

class RemoteCamera(EventDispatcher):
    url = StringProperty()
    frame_no = NumericProperty(0)

    # ==============================
    # Main thread
    # ==============================

    def __init__(self, **kwargs):
        super(RemoteCamera, self).__init__(**kwargs)
        self.running = False

    def start(self):
        if self.running:
            Logger.info('RemoteCamera: WARNING: called start(), but camera already running')
            return
        self.running = True
        self.thread = threading.Thread(target=self.run, name='RemoteCamera')
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if not self.running:
            Logger.info('RemoteCamera: WARNING: called stop() but camera is not running')
            return
        self.running = False

    @mainthread
    def set_status(self, status):
        self.status = status

    # ==============================
    # RemoteCamera thread
    # ==============================

    def run(self):
        Logger.info('RemoteCamera: thread started')
        while self.running:
            print 'hello, frame', self.frame_no
            time.sleep(1)
            self.frame_no += 1
        Logger.info('RemoteCamera: stop')
