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
from werkzeug.utils import EnvironHeaders, cached_property, Href
from werkzeug.utils import create_environ, url_encode
from werkzeug.http import parse_cache_control_header, HeaderSet
from werkzeug.test import Client

from MoinMoin import config

from MoinMoin import log
logging = log.getLogger(__name__)

class MoinMoinFinish(Exception):
    """ Raised to jump directly to end of run() function, where finish is called """

class Request(WerkzeugRequest, WerkzeugResponse):
    """ A full featured Request/Response object.

    To better distinguish incoming and outgoing data/headers,
    incoming versions are prefixed with 'in_' in contrast to
    original Werkzeug implementation.
    """
    charset = config.charset
    encoding_errors = 'replace'
    default_mimetype = 'text/html'
    given_config = None # if None, load wiki config from disk

    def __init__(self, environ, populate_request=True, shallow=False,
                 response=None, status=None, headers=None, mimetype=None,
                 content_type=None):
        WerkzeugRequest.__init__(self, environ, populate_request, shallow)
        WerkzeugResponse.__init__(self, response, status, headers,
                                  mimetype, content_type)
        if self.script_root:
            self.href = Href(self.script_root, self.charset)
        else:
            self.href = Href('/', self.charset)
        self.abs_href = Href(self.url_root, self.charset)

    data = WerkzeugResponse.data
    stream = WerkzeugResponse.stream
    cache_control = WerkzeugResponse.cache_control

    def in_cache_control(self):
        """A `CacheControl` object for the incoming cache control headers."""
        cache_control = self.environ.get('HTTP_CACHE_CONTROL')
        return parse_cache_control_header(cache_control)
    in_cache_control = cached_property(in_cache_control)

    def in_headers(self):
        """The headers from the WSGI environ as immutable `EnvironHeaders`."""
        return EnvironHeaders(self.environ)
    in_headers = cached_property(in_headers, doc=WerkzeugRequest.headers.__doc__)

    def in_stream(self):
        """The parsed stream if the submitted data was not multipart or
        urlencoded form data.  This stream is the stream left by the CGI
        module after parsing.  This is *not* the WSGI input stream.
        """
        if self._data_stream is None:
            self._load_form_data()
        return self._data_stream
    in_stream = property(in_stream, doc=WerkzeugRequest.stream.__doc__)

    def in_data(self):
        """This reads the buffered incoming data from the client into the
        string.  Usually it's a bad idea to access `data` because a client
        could send dozens of megabytes or more to cause memory problems on the
        server.
        """
        return self.in_stream.read()
    in_data = cached_property(in_data, doc=WerkzeugRequest.data.__doc__)

class TestRequest(Request):
    """ Request with customized `environ` for test purposes. """
    def __init__(self, path="/", query_string=None, method='GET',
                 content_type=None, content_length=0, form_data=None,
                 environ_overrides=None):
        """
        For parameter reference see the documentation of the werkzeug.utils
        package, especially the functions `url_encode` and `create_environ`.
        """
        input_stream = None

        if form_data is not None:
            form_data = url_encode(form_data)
            content_type = 'application/x-www-form-urlencoded'
            content_length = len(form_data)
            input_stream = StringIO(form_data)
        environ = create_environ(path=path, query_string=query_string,
                                 method=method, input_stream=input_stream,
                                 content_type=content_type,
                                 content_length=content_length)

        environ['HTTP_USER_AGENT'] = 'MoinMoin/TestRequest'
        # must have reverse lookup or tests will be extremely slow:
        environ['REMOTE_ADDR'] = '127.0.0.1'

        if environ_overrides:
            environ.update(environ_overrides)

        super(TestRequest, self).__init__(environ)

def evaluate_request(request):
    """ Evaluate a request and returns a tuple of application iterator,
    status code and list of headers. This method is meant for testing
    purposes.
    """
    output = []
    headers_set = []
    def start_response(status, headers, exc_info=None):
        headers_set[:] = [status, headers]
        return output.append
    result = request(request.environ, start_response)

    # any output via (WSGI-deprecated) write-callable?
    if output:
        result = output
    return (result, headers_set[0], headers_set[1])
