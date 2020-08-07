import re
from kivy.properties import ConfigParserProperty
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

Builder.load_string('''
<ImgFileName>:
    pos: (root.x, root.y)
    size_hint_y: None
    height: sp(80)
    orientation: 'vertical'

    TextInput:
        font_size: sp(13)
        text: root.last_image
        multiline: False
        on_focus: root.last_image = self.text

    BoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: "30dp"
        Widget:
            size_hint_x: None
            width: '25dp'
        IconButton:
            icon: 'fa-minus'
            font_size: "25dp"
            on_release: root.last_image_inc(-1)
        IconButton:
            icon: "fa-plus"
            font_size: "25dp"
            on_release: root.last_image_inc(+1)
    FlatButton:
        text: 'Load'
        on_release: root.load_image()
''')

class ImgFileName(BoxLayout):
    CANON_REGEXP = re.compile(r'IMG_([0-9]+).JPG')
    NIKON_REGEXP = re.compile(r'DSC_([0-9]+).JPG')
    last_image = ConfigParserProperty('', 'tracker', 'last_image', 'app')

    def last_image_inc(self, step=1):
        m = self.CANON_REGEXP.match(self.last_image)
        if m:
            n = int(m.group(1))
            n += step
            self.last_image = 'IMG_%d.JPG' % n

        m = self.NIKON_REGEXP.match(self.last_image)
        if m:
            n = int(m.group(1))
            n += step
            self.last_image = 'DSC_%04d.JPG' % n

    def load_image(self):
        pass
