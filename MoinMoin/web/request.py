# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - New slimmed down WSGI Request.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import re

from werkzeug import wrappers as werkzeug
from werkzeug.utils import cached_property

from MoinMoin import config

from MoinMoin import log
logging = log.getLogger(__name__)

class Request(werkzeug.Request):
    charset = config.charset
    encoding_errors = 'replace'
