# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - http authentication

    You need either your webserver configured for doing HTTP auth (like Apache
    reading some .htpasswd file) or Twisted (will accept HTTP auth against
    password stored in moin user profile, but currently will NOT ask for auth)
    or Standalone (in which case it will ask for auth and accept auth against
    stored user profile.)

    @copyright: 2006 MoinMoin:ThomasWaldmann
                2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config, user
from MoinMoin.auth import BaseAuth
from base64 import decodestring

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
            return user_obj, True

        authobj = request.authorization
        if authobj:
            u = user.User(request, auth_username=authobj.username,
                          auth_method=self.name, auth_attribs=('name', 'password'))

        if u and self.autocreate:
            u.create_or_update()
        if u and u.valid:
            return u, True # True to get other methods called, too
        else:
            return user_obj, True
