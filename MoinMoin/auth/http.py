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
from MoinMoin.request import request_twisted, request_cli, request_standalone
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

        # for standalone, request authorization and verify it,
        # deny access if it isn't verified
        if isinstance(request, request_standalone.Request):
            request.setHttpHeader('WWW-Authenticate: Basic realm="MoinMoin"')
            auth = request.headers.get('Authorization')
            if auth:
                auth = auth.split()[-1]
                info = decodestring(auth).split(':', 1)
                if len(info) == 2:
                    u = user.User(request, auth_username=info[0], password=info[1],
                                  auth_method=self.name, auth_attribs=[])
            if not u:
                request.makeForbidden(401, _('You need to log in.'))
        # for Twisted, just check
        elif isinstance(request, request_twisted.Request):
            username = request.twistd.getUser().decode(config.charset)
            password = request.twistd.getPassword().decode(config.charset)
            # when using Twisted http auth, we use username and password from
            # the moin user profile, so both can be changed by user.
            u = user.User(request, auth_username=username, password=password,
                          auth_method=self.name, auth_attribs=())
        elif not isinstance(request, request_cli.Request):
            env = request.env
            auth_type = env.get('AUTH_TYPE', '').lower()
            if auth_type in ['basic', 'digest', 'ntlm', 'negotiate', ]:
                username = env.get('REMOTE_USER', '').decode(config.charset)
                if auth_type in ('ntlm', 'negotiate', ):
                    # converting to standard case so the user can even enter wrong case
                    # (added since windows does not distinguish between e.g.
                    #  "Mike" and "mike")
                    username = username.split('\\')[-1] # split off domain e.g.
                                                        # from DOMAIN\user
                    # this "normalizes" the login name from {meier, Meier, MEIER} to Meier
                    # put a comment sign in front of next line if you don't want that:
                    username = username.title()
                # when using http auth, we have external user name and password,
                # we don't use the moin user profile for those attributes.
                u = user.User(request, auth_username=username,
                              auth_method=self.name, auth_attribs=('name', 'password'))

        if u and self.autocreate:
            u.create_or_update()
        if u and u.valid:
            return u, True # True to get other methods called, too
        else:
            return user_obj, True
