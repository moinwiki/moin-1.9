# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - http authentication

    You need your webserver configured for doing authentication (like Apache
    reading some .htpasswd file and requesting http basic auth) and pass the
    authenticated username as REMOTE_USER environment var.

    @copyright: 2006-2009 MoinMoin:ThomasWaldmann
                2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, user
from MoinMoin.auth import BaseAuth

class HTTPAuth(BaseAuth):
    """ authenticate via http basic/digest/ntlm auth """
    name = 'http'

    def __init__(self, autocreate=False):
        self.autocreate = autocreate
        BaseAuth.__init__(self)

    def request(self, request, user_obj, **kw):
        u = None
        _ = request.getText
        # always revalidate auth
        if user_obj and user_obj.auth_method == self.name:
            user_obj = None
        # something else authenticated before us
        if user_obj:
            logging.debug("already authenticated, doing nothing")
            return user_obj, True

        auth_username = request.remote_user
        logging.debug("REMOTE_USER = %r" % auth_username)
        if auth_username:
            u = user.User(request, auth_username=auth_username.decode('utf-8'), # XXX correct?
                          auth_method=self.name, auth_attribs=('name', 'password'))

        if u and self.autocreate:
            u.create_or_update()
        if u and u.valid:
            return u, True # True to get other methods called, too
        else:
            return user_obj, True

