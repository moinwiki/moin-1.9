# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - HTTP exceptions

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

from werkzeug import exceptions

class SurgeProtection(exceptions.ServiceUnavailable):
    name = 'Surge protection'
    description = (
        "<strong>Warning:</strong>"
        "<p>You triggered the wiki's surge protection by doing too many requests in a short time.</p>"
        "<p>Please make a short break reading the stuff you already got.</p>"
        "<p>When you restart doing requests AFTER that, slow down or you might get locked out for a longer time!</p>"
    )
    
    def __init__(self, retry_after=3600):
        ServiceUnavailable.__init__(self)
        self.retry_after = retry_after

    def get_headers(self, environ):
        headers = ServiceUnavailable.get_headers(self, environ)
        headers.append(('Retry-After', '%d' % self.retry_after))
        return headers

class Forbidden(exceptions.Forbidden):
    description = "<p>You are not allowed to access this!</p>"

class PageNotFound(exceptions.NotFound):
    pass
