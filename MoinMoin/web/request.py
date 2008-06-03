# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - New slimmed down WSGI Request.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import re

from werkzeug.wrappers import Request as WerkzeugRequest
from werkzeug.wrappers import Response as WerkzeugResponse

from MoinMoin import config

from MoinMoin import log
logging = log.getLogger(__name__)

class Request(WerkzeugRequest):
    charset = config.charset
    encoding_errors = 'replace'

class Response(WerkzeugResponse):
    charset = config.charset
    default_mimetype = 'text/html'
    
