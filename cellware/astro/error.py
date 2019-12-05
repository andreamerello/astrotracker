from kivy.lang import Builder
from kivy.base import ExceptionHandler, ExceptionManager
from kivy.uix.popup import Popup
from kivy.properties import StringProperty

Builder.load_string("""
<MessageBox>:

    size_hint: 0.95, None
    height: app.std_height * 12

    BoxLayout:
        orientation: 'vertical'

        Label:
            text: root.message
            size_hint_y: 1

        Label:
            text: root.description

        Button:
            text: 'OK'
            size_hint_y: None
            height: app.std_height
            on_release: root.dismiss()
""")
class MessageBox(Popup):
    message = StringProperty()
    description = StringProperty()


class ErrorMessage(Exception):
    """
    This represents a non-fatal exception: the error message will be displayed
    to the user in an error box, and the execution of the app will continue
    """

    def __init__(self, message, description=''):
        self.message = message
        self.description = description


class MyExceptionHandler(ExceptionHandler):

    def __init__(self, add_handler=True):
        if add_handler:
            ExceptionManager.add_handler(self)

    def handle_exception(self, exc):
        if isinstance(exc, ErrorMessage):
            self.show_error(exc.message, exc.description)
            return ExceptionManager.PASS
        return ExceptionManager.RAISE

    def show_error(self, message, description):
        box = MessageBox(title='Error', message=message, description=description)
        box.open()
