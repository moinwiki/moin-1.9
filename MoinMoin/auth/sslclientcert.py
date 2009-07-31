# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SSL client certificate authentication

    Currently not supported for Twisted web server, but only for web servers
    setting SSL_CLIENT_* environment (e.g. Apache).

    @copyright: 2003 Martin v. Loewis,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config, user
from MoinMoin.auth import BaseAuth

class SSLClientCertAuth(BaseAuth):
    """ authenticate via SSL client certificate """

    name = 'sslclientcert'

    def __init__(self, authorities=None,
                 email_key=True, name_key=True,
                 use_email=False, use_name=False,
                 autocreate=False):
        self.use_email = use_email
        self.authorities = authorities
        self.email_key = email_key
        self.name_key = name_key
        self.use_email = use_email
        self.use_name = use_name
        self.autocreate = autocreate
        BaseAuth.__init__(self)

    def request(self, request, user_obj, **kw):
        u = None
        changed = False

        env = request.environ
        if env.get('SSL_CLIENT_VERIFY', 'FAILURE') == 'SUCCESS':

            # check authority list if given
            if self.authorities and env.get('SSL_CLIENT_I_DN_OU') in self.authorities:
                return user_obj, True

            email_lower = None
            if self.email_key:
                email = env.get('SSL_CLIENT_S_DN_Email', '').decode(config.charset)
                email_lower = email.lower()
            commonname_lower = None
            if self.name_key:
                commonname = env.get('SSL_CLIENT_S_DN_CN', '').decode(config.charset)
                commonname_lower = commonname.lower()
            if email_lower or commonname_lower:
                for uid in user.getUserList(request):
                    u = user.User(request, uid,
                                  auth_method=self.name, auth_attribs=())
                    if self.email_key and email_lower and u.email.lower() == email_lower:
                        u.auth_attribs = ('email', 'password')
                        if self.use_name and commonname_lower != u.name.lower():
                            u.name = commonname
                            changed = True
                            u.auth_attribs = ('email', 'name', 'password')
                        break
                    if self.name_key and commonname_lower and u.name.lower() == commonname_lower:
                        u.auth_attribs = ('name', 'password')
                        if self.use_email and email_lower != u.email.lower():
                            u.email = email
                            changed = True
                            u.auth_attribs = ('name', 'email', 'password')
                        break
                else:
                    u = None
                if u is None:
                    # user wasn't found, so let's create a new user object
                    u = user.User(request, name=commonname_lower, auth_username=commonname_lower,
                                  auth_method=self.name)
                    u.auth_attribs = ('name', 'password')
                    if self.use_email:
                        u.email = email
                        u.auth_attribs = ('name', 'email', 'password')
        elif user_obj and user_obj.auth_method == self.name:
            user_obj.valid = False
            return user_obj, False
        if u and self.autocreate:
            u.create_or_update(changed)
        if u and u.valid:
            return u, True
        else:
            return user_obj, True
