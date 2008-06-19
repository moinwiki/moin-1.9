# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - New slimmed down WSGI Request.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import re

from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response as WerkzeugResponse
from werkzeug.utils import EnvironHeaders, cached_property

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
