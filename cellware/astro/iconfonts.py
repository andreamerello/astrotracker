from kivy.resources import resource_find
from kivy.garden import iconfonts
from kivy.logger import Logger

def init():
    css = resource_find('data/font-awesome.css')
    fontd = resource_find('data/font-awesome.fontd')
    ttf = resource_find('data/font-awesome.ttf')
    if not fontd:
        Logger.info('Container: Generating font-awesome.fontd')
        fontd = css.replace('.css', '.fontd')
        iconfonts.create_fontdict_file(css, fontd)
    iconfonts.register('default_font', ttf, fontd)
