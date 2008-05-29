# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Context objects which are passed thru instead of the classic
               request objects. Currently contains legacy wrapper code for
               a single request object.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import re

from werkzeug.utils import Headers

from MoinMoin.request import RequestBase
from MoinMoin.web.request import Request

from MoinMoin import log
logging = log.getLogger(__name__)

STATUS_CODE_RE = re.compile('Status:\s*(\d{3,3})', re.IGNORECASE)

class Context(object):
    pass

class HTTPContext(Context, RequestBase):
    """ Lowermost context for MoinMoin.

    Contains code related to manipulation of HTTP related data like:
    * Headers
    * Cookies
    * GET/POST/PUT/etc data 
    """
    def __init__(self, environ):
        self._wsgirequest = Request(environ)
        self.__output = []
        self.headers = Headers()

        self.status = 200
        self.failed = 0

        self._setup_vars_from_std_env(environ)
        RequestBase.__init__(self, {})

    # implementation of methods expected by RequestBase
    def _setup_args_from_cgi_form(self):
        logging.warning("Form values requested as plain dict, "
                        "consider using MultiDicts here")
        return self._wsgirequest.form.to_dict(flat=False)

    def read(self, n=None):
        if n is None:
            return self._wsgirequest.data
        else:
            return self._wsgirequest.input_stream.read(n)

    def send_file(self, fileobj, bufsize=8192, do_flush=None):
        self._sendfile = fileobj
        self._send_bufsize = bufsize

    def write(self, *data):
        if len(data) > 1:
            logging.warning("Some code still uses write with multiple arguments, "
                            "consider changing this soon")
        self.__output.extend(data)

    def output(self):
        return ''.join(self.__output)

    def _emit_http_headers(self, headers):
        print 'called', headers
        st_header, other_headers = headers[0], headers[1:]
        status = STATUS_CODE_RE.match(st_header)
        status = int(status.groups()[0])
        self.status = status
        for header in other_headers:
            key, value = header.split(':', 1)
            self.headers.add(key, value)

    def flush(self):
        pass

    def setup_args(self):
        return self._wsgirequest.values.to_dict(flat=False)

# mangle in logging of function calls

def _logfunc(func):
    def _decorated(*args, **kwargs):
        logging.warning("Function '%s' called with '%r', '%r'. Consider if"
                        "this is intended", func.__name__, args, kwargs)
        return func(*args, **kwargs)
    _decorated.__name__ = func.__name__
    _decorated.__doc__ = func.__doc__
    return _decorated

from types import FunctionType

for name, item in RequestBase.__dict__.items():
    if isinstance(item, FunctionType):
        setattr(RequestBase, name, _logfunc(item))
del name, item, FunctionType, _logfunc
