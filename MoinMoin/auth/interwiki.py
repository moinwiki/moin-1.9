# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - authentication using a remote wiki

    @copyright: 2005 by Florian Festi,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

verbose = False

import xmlrpclib
from MoinMoin import auth, wikiutil, user
from MoinMoin.auth import BaseAuth

class InterwikiAuth(BaseAuth):
    name = 'interwiki'
    logout_possible = True
    login_inputs = ['username', 'password']

    def __init__(self, trusted_wikis):
        BaseAuth.__init__(self)
        self.trusted_wikis = trusted_wikis

    def login(self, request, user_obj, **kw):
        username = kw.get('username')
        password = kw.get('password')

        if not username or not password:
            return user_obj, True, None, None

        if verbose: request.log("interwiki auth: trying to auth %r" % username)
        username = username.replace(' ', ':', 1) # Hack because ':' is not allowed in name field
        wikitag, wikiurl, name, err = wikiutil.resolve_wiki(request, username)

        if verbose: request.log("interwiki auth: resolve wiki returned: %r %r %r %r" % (wikitag, wikiurl, name, err))
        if err or wikitag not in self.trusted_wikis:
            return user_obj, True, None, None

        homewiki = xmlrpclib.Server(wikiurl + "?action=xmlrpc2")
        account_data = homewiki.getUser(name, password)
        if isinstance(account_data, str):
            if verbose: request.log("interwiki auth: %r wiki said: %s" % (wikitag, account_data))
            return user_obj, True, None, account_data

        # TODO: check remote auth_attribs
        u = user.User(request, name=name, auth_method=self.name, auth_attribs=('name', 'aliasname', 'password', 'email', ))
        for key, value in account_data.iteritems():
            if key not in request.cfg.user_transient_fields:
                setattr(u, key, value)
        u.valid = True
        u.create_or_update(True)
        if verbose: request.log("interwiki: successful auth for %r" % name)
        return u, True, None, None
