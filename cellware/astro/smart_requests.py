import traceback
import requests
from requests import RequestException
from kivy.utils import platform
from kivy.logger import Logger
from astro.error import ErrorMessage

DESCRIPTION = """
Check that the device is connected to the correct WiFi network
"""

class SmartRequests(object):
    """
    Like requests, but it always print a traceback on exception and raises on
    400s and 500s status codes
    """

    def __init__(self, app):
        self.app = app

    def do_smart_request(self, method, *args, **kwargs):
        error_message = kwargs.pop('error', '')
        kwargs.setdefault('timeout', self.app.get_timeout())

        meth = getattr(requests, method)
        try:
            resp = meth(*args, **kwargs)
            resp.raise_for_status()
            return resp
        except RequestException as e:
            Logger.exception('SmartRequests exception')
            raise ErrorMessage(error_message, DESCRIPTION)

    def get(self, *args, **kwargs):
        return self.do_smart_request('get', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.do_smart_request('put', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.do_smart_request('post', *args, **kwargs)
