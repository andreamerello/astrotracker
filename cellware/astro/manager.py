from kivy.uix.screenmanager import (ScreenManager, Screen,
                                    FallOutTransition, RiseInTransition)
from kivy.uix.behaviors.focus import FocusBehavior

class Manager(ScreenManager):
    def __init__(self):
        super(Manager, self).__init__()
        self.history = []

    def ensure_unique_name(self, view):
        basename = view.name
        name = basename
        i = 0
        while name in self.screen_names:
            name = '%s-%d' % (basename, i)
            i += 1
        view.name = name

    def open(self, view):
        self.ensure_unique_name(view)
        self.unfocus_maybe()
        name = view.name
        if self.has_screen(name):
            self.remove_widget(self.get_screen(name))
        self.add_widget(view)
        self.transition = RiseInTransition()
        self.current = name
        self.history.append(view)

    def unwind(self, name):
        while self.current_view.name != name:
            res = self.go_back()
            if not res:
                # we reached the bottom without finding the target screen,
                # bail out
                break

    def go_back(self):
        if len(self.history) < 2:
            return False
        view = self.history.pop()
        if hasattr(view, 'close'):
            view.close()
        self.transition = FallOutTransition()
        self.current = self.history[-1].name
        return True

    def unfocus_maybe(self):
        if not self.history:
            return
        screen = self.history[-1]
        for widget in screen.walk():
            if isinstance(widget, FocusBehavior):
                widget.focus = False

    @property
    def current_view(self):
        return self.history[-1]

    def on_key_press(self, app, k):
        if hasattr(self.current_view, 'on_key_press'):
            self.current_view.on_key_press(app, k)
