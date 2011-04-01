# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - logging auth plugin

    This does nothing except logging the auth parameters.
    Be careful with the logs, they contain sensitive data.
    Do not use this except for debugging auth problems.

    @copyright: 2006-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.auth import BaseAuth, ContinueLogin

class AuthLog(BaseAuth):
    """ just log the call, do nothing else """
    name = "log"

    def log(self, request, action, user_obj, kw):
        logging.info('%s: user_obj=%r kw=%r' % (action, user_obj, kw))

    def login(self, request, user_obj, **kw):
        self.log(request, 'login', user_obj, kw)
        return ContinueLogin(user_obj)

    def request(self, request, user_obj, **kw):
        self.log(request, 'session', user_obj, kw)
        return user_obj, True

    def logout(self, request, user_obj, **kw):
        self.log(request, 'logout', user_obj, kw)
        return user_obj, True
