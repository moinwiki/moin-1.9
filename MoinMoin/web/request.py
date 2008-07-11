# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - New slimmed down WSGI Request.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import re
from StringIO import StringIO

from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response as WerkzeugResponse
from werkzeug.utils import EnvironHeaders, cached_property
from werkzeug.utils import create_environ, url_encode
from werkzeug.http import parse_cache_control_header

from MoinMoin import config

from MoinMoin import log
logging = log.getLogger(__name__)

class Request(WerkzeugRequest, WerkzeugResponse):
    """ A full featured Request/Response object.

    To better distinguish incoming and outgoing data/headers,
    incoming versions are prefixed with 'in_' in contrast to
    original Werkzeug implementation.
    """
    charset = config.charset
    encoding_errors = 'replace'
    default_mimetype = 'text/html'

    def __init__(self, environ, populate_request=True, shallow=False,
                 response=None, status=None, headers=None, mimetype=None,
                 content_type=None):
        WerkzeugRequest.__init__(self, environ, populate_request, shallow)
        WerkzeugResponse.__init__(self, response, status, headers,
                                  mimetype, content_type)

    data = WerkzeugResponse.data
    stream = WerkzeugResponse.stream
    cache_control = WerkzeugResponse.cache_control

    def in_cache_control(self):
        cache_control = self.environ.get('HTTP_CACHE_CONTROL')
        return parse_cache_control_header(cache_control)
    in_cache_control = cached_property(in_cache_control)

    def in_headers(self):
        return EnvironHeaders(self.environ)
    in_headers = cached_property(in_headers, doc=WerkzeugRequest.headers.__doc__)

    def in_stream(self):
        if self._data_stream is None:
            self._load_form_data()
        return self._data_stream
    in_stream = property(in_stream, doc=WerkzeugRequest.stream.__doc__)

    def in_data(self):
        return self.in_stream.read()
    in_data = cached_property(in_data, doc=WerkzeugRequest.data.__doc__)

class TestRequest(Request):
    def __init__(self, path="/", query_string=None, method='GET',
                 input_stream=None, content_type=None, content_length=0,
                 form_data=None, **env):
        self.errors_stream = StringIO()
        self.output_stream = StringIO()

        if form_data is not None:
            form_data = url_encode(form_data)
            content_type = 'application/x-www-form-urlencoded'
            content_length = len(form_data)
            input_stream = StringIO(form_data)
        environ = create_environ(path=path, query_string=query_string,
                                 method=method, input_stream=input_stream,
                                 content_type=content_type,
                                 content_length=content_length,
                                 errors_stream=self.errors_stream)

        for k, v in env.items():
            environ[k] = v

        environ['HTTP_USER_AGENT'] = 'MoinMoin/TestRequest'
        super(TestRequest, self).__init__(environ)

    def __call__(self):
        def start_response(status, headers, exc_info=None):
            return self.output_stream.write

        appiter = Request.__call__(self, self.environ, start_response)
        for s in appiter:
            self.output_stream.write(s)
        return self.output_stream.getvalue()

    def output(self):
        """ Content of the WSGI output stream. """
        return self.output_stream.getvalue()
    output = property(output, doc=output.__doc__)

    def errors(self):
        """ Content of the WSGI error stream. """
        return self.errors_stream.getvalue()
    errors = property(errors, doc=errors.__doc__)
