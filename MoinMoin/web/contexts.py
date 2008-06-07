# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Context objects which are passed thru instead of the classic
               request objects. Currently contains legacy wrapper code for
               a single request object.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import re, time, inspect

from werkzeug.utils import Headers, http_date

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
        self.environ = environ
        self.__output = []
        self.headers = Headers()

        self.status = 200

        # compat properties (remove when not necessary anymore)
        self._auth_redirected = False
        self.forbidden = 0
        self._cache_disabled = 0
        self.page = None
        self.user_headers = []
        self.sent_headers = None
        self.writestack = []

    # implementation of methods expected by RequestBase
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

    def __getattr__(self, name):
        logging.debug("Proxying to '%r' for attribute '%s'",
                      self._wsgirequest, name)
        return getattr(self._wsgirequest, name)

    def __setattr__(self, name, value):
        stack = inspect.stack()
        parent = stack[1]
        caller, filename, lineno = parent[3], parent[1], parent[0].f_lineno
        logging.debug("Setting attribute '%s' to value '%r' by '%s' "
                      "in file '%s',line '%s'", name, value, caller,
                      filename, lineno)
        self.__dict__[name] = value
    
    # compatibility wrapping
    def cookie(self):
        return self._wsgirequest.cookies
    cookie = property(cookie)

    def script_name(self):
        return self._wsgirequest.script_root
    script_name = property(script_name)

    def request_method(self):
        return self._wsgirequest.method
    request_method = property(request_method)

    def path_info(self):
        return self._wsgirequest.path
    path_info = property(path_info)

    def is_ssl(self):
        return self._wsgirequest.is_secure
    is_ssl = property(is_ssl)
    

    def setHttpHeader(self, header):
        header, value = header.split(':', 1)
        self.headers.add(header, value)

    def disableHttpCaching(self, level=1):
        if level <= self._cache_disabled:
            return
        
        if level == 1:
            self.headers.add('Cache-Control', 'private, must-revalidate, mag-age=10')
        elif level == 2:
            self.headers.add('Cache-Control', 'no-cache')
            self.headers.set('Pragma', 'no-cache')

        if not self._cache_disabled:
            when = time.time() - (3600 * 24 * 365)
            self.headers.set('Expires', http_date(when))

        self._cache_disabled = level

    def _get_dicts(self):
        if not hasattr(self, '_dicts'):
            from MoinMoin import wikidicts
            dicts = wikidicts.GroupDict(self)
            dicts.load_dicts()
            self._dicts = dicts
        return self._dicts

    def _del_dicts(self):
        del self._dicts

    dicts = property(_get_dicts, None, _del_dicts)
    del _get_dicts, _del_dicts

    def finish(self):
        pass

# mangle in logging of function calls
def _logfunc(func):
    def _decorated(*args, **kwargs):
        stack = inspect.stack()
        parent = stack[1]
        caller, filename, lineno = parent[3], parent[1], parent[0].f_lineno
        logging.warning("Function '%s' called by '%s' in file '%s', line '%s'",
                        func.__name__, caller, filename, lineno)
        return func(*args, **kwargs)
    _decorated.__name__ = func.__name__
    _decorated.__doc__ = func.__doc__
    return _decorated

from types import FunctionType

for name, item in RequestBase.__dict__.items():
   if isinstance(item, FunctionType):
       setattr(RequestBase, name, _logfunc(item))
del name, item, FunctionType, _logfunc

