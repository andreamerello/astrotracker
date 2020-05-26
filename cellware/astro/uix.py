from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.animation import Animation
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import Screen
from kivy.uix.popup import Popup
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.scatterlayout import ScatterLayout
from kivy.utils import get_color_from_hex


class AbstractTheme(object):

    @classmethod
    def status(cls, s):
        s = s.upper()
        return getattr(cls, s)

    @classmethod
    def bgstatus(cls, s):
        s = 'BG' + s.upper()
        return getattr(cls, s)


class BootstrapTheme(AbstractTheme):
    BG = get_color_from_hex("#FFFFFF") # white
    SEPARATOR = get_color_from_hex("#CCCCCC")
    ICON = get_color_from_hex("#000000") # black
    TRANSPARENT = get_color_from_hex("#FFFFFF00")

    # status classes, inspired by bootstrap CSS
    MUTED   = get_color_from_hex("#777777") # gray
    PRIMARY = get_color_from_hex("#0D47A1") # 900 color from material design
    SUCCESS = get_color_from_hex("#00CC00") # green
    INFO    = get_color_from_hex("#31708f") # blueish
    WARNING = get_color_from_hex("#CCCC00") # yellow
    DANGER  = get_color_from_hex("#FF0000") # red

    BGMUTED   = BG
    BGPRIMARY = get_color_from_hex("#337ab7")
    BGSUCCESS = get_color_from_hex("#dff0d8")
    BGWARNING = get_color_from_hex("#fcf8e3")
    BGDANGER  = get_color_from_hex("#f2dede")
    BGINFO    = get_color_from_hex("#d9edf7")


class MDBootstrapTheme(BootstrapTheme):
    # colors taken from:
    #   http://mdbootstrap.com/css/colors/
    #   http://mdbootstrap.com/css/helpers/
    WHITE   = get_color_from_hex("#FFFFFF")
    MUTED   = get_color_from_hex("#777777")
    PRIMARY = get_color_from_hex("#4285F4")
    SUCCESS = get_color_from_hex("#00C851")
    INFO    = get_color_from_hex("#33b5e5")
    WARNING = get_color_from_hex("#ffbb33")
    DANGER =  get_color_from_hex("#ff4444")

Theme = MDBootstrapTheme



Builder.load_string("""
<MyLabel>:
    canvas.before:
        Color:
            rgba: self.bgcolor or Theme.TRANSPARENT
        Rectangle:
            pos: self.pos
            size: self.size

    bgcolor: Theme.BG
    color: Theme.ICON
    font_size: app.font_size

<MyScreen>:
    canvas.before:
        Color:
            rgba: self.bgcolor or Theme.TRANSPARENT
        Rectangle:
            pos: self.pos
            size: self.size

    bgcolor: Theme.BG

<Paragraph>:
    # maximize the width of the label, but let the height growing
    # automatically; scale is used to animate: set it to 0 to hide the label,
    # and to 1 to fully show it
    scale: 1
    size_hint_y: None
    text_size: self.width, None
    height: self.texture_size[1] * self.scale
    #
    halign: "left"
    valign: "middle"
    padding: [dp(5), dp(5)]

<FlatButton>:
    background_color: (1, 1, 1, 1)
    _down_color: darker(self.background_color)
    color: Theme.PRIMARY
    disabled_color: Theme.MUTED
    show_border: True
    font_size: app.font_size

    canvas.before:
        Color:
            rgba: self.background_color if self.state == 'normal' else self._down_color

        Rectangle:
            pos: self.pos
            size: self.size

        Color:
            rgba: Theme.SEPARATOR if self.show_border else Theme.TRANSPARENT

        Line:
            rectangle: self.x+1,self.y+1,self.width-1,self.height-1


<IconButton@FlatButton>:
    icon: ""
    markup: True
    show_border: False
    color: Theme.ICON
    text: icon(self.icon) if self.icon else ""
    size_hint_x: None
    width: self.height

""")


class FlatButton(ButtonBehavior, Label):
    pass

class MyLabel(Label):
    pass

class MyScreen(Screen):
    pass

class Paragraph(MyLabel):

    # we can have four different states:
    # VISIBLE   ANIM      MEANING
    # True      <...>     in process of being shown
    # True      None      fully shown
    # False     <...>     in process of being hidden
    # False     None      fully hidden
    anim = None
    visible = False

    def _on_complete(self, anim, widget):
        self.anim = None

    def _start(self, anim):
        if self.anim:
            self.anim.cancel(self)
        #
        self.anim = anim
        self.anim.bind(on_complete=self._on_complete)
        self.anim.start(self)

    def show(self, text, duration=0.3):
        self.text = text
        if self.visible:
            return
        # animate from hidden to shown
        self.visible = True
        anim = Animation(scale=1, duration=duration)
        anim.name = 'show'
        self._start(anim)

    def hide(self, duration=0.3):
        if not self.visible:
            return
        #
        def cleartext(anim, widget):
            self.text = ''
        #
        self.visible = False
        anim = Animation(scale=0, duration=duration)
        anim.bind(on_complete=cleartext)
        anim.name = 'hide'
        self._start(anim)

def darker(color, factor=0.5):
    r, g, b, a = color
    r *= factor
    g *= factor
    b *= factor
    return r, g, b, a


class MyScatterPlaneLayout(ScatterLayout):
    # the ScatterPlaneLayout which is distributed with kivy 1.9.1 seems buggy:
    # it inherits from ScatterPlane instead of ScatterLayout. This is
    # supposedly the correct version
    def collide_point(self, x, y):
        return True
