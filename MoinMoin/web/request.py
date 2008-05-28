# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - New slimmed down WSGI Request.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

from werkzeug import wrappers as werkzeug
from werkzeug.utils import cached_property

from MoinMoin.request import RequestBase

from MoinMoin import log
logging = log.getLogger(__name__)

class Request(werkzeug.Request, RequestBase):
    def __init__(self, environ):
        werkzeug.Request.__init__(self, environ)
        RequestBase.__init__(self, {})

    def __getattribute__(self, name):
        logging.error("UR DOING IT WRONG! (attribute '%s' requested)", name)
        return RequestBase.__getattribute__(self, name)

    def __setattr__(self, name, value):
        logging.error("UR DOING IT WRONG! (attribute '%s' changed to '%r')", name, value)
        return RequestBase.__setattr__(self, name, value)

    def __delattr__(self, name):
        logging.error("UR DOING IT WRONG! (attribute '%s' deleted)", name)
        return Request.__delattr__(self, name)        

    def decodePagename(self, name):
        return name

    def request_uri(self):
        answer = self.script_root + self.path
        qs = self.query_string
        if qs:
            answer = answer + '?' + qs
        return answer
    request_uri = cached_property(request_uri)

    def http_user_agent(self):
        return str(self.user_agent)
    http_user_agent = cached_property(http_user_agent)

for moinname, werkname in [('path_info', 'path'),
                           ('request_method', 'method')]:
    method =  getattr(werkzeug.Request, werkname)
    setattr(Request, moinname, method)
del moinname, werkname
        

    

