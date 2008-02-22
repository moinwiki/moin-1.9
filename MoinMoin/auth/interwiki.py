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
from MoinMoin.auth import BaseAuth, ContinueLogin, CancelLogin

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
            return ContinueLogin(user_obj)

        if verbose: request.log("interwiki auth: trying to auth %r" % username)
        wikiname, username = username.split(' ', 1) # XXX Hack because ':' is not allowed in name field
        wikitag, wikiurl, name, err = wikiutil.resolve_interwiki(request, wikiname, username)

        if verbose: request.log("interwiki auth: resolve wiki returned: %r %r %r %r" % (wikitag, wikiurl, name, err))
        if err or wikitag not in self.trusted_wikis:
            return ContinueLogin(user_obj)

        homewiki = xmlrpclib.ServerProxy(wikiurl + "?action=xmlrpc2")
        auth_token = homewiki.getAuthToken(name, password)
        if not auth_token:
            if verbose: request.log("interwiki auth: %r wiki did not return an auth token." % wikitag)
            return ContinueLogin(user_obj)

        if verbose: request.log("interwiki: successfully got an auth token for %r" % name)
        if verbose: request.log("interwiki: trying to get user profile data for %r" % name)

        mc = xmlrpclib.MultiCall(homewiki)
        mc.applyAuthToken(auth_token)
        mc.getUserProfile()
        result, account_data = mc()

        if result != "SUCCESS":
            if verbose: request.log("interwiki auth: %r wiki did not accept auth token." % wikitag)
            return ContinueLogin(None)

        if not account_data:
            if verbose: request.log("interwiki auth: %r wiki did not return a user profile." % wikitag)
            return ContinueLogin(None)

        if verbose: request.log("interwiki auth: %r wiki returned a user profile." % wikitag)

        # TODO: check remote auth_attribs
        u = user.User(request, name=name, auth_method=self.name, auth_attribs=('name', 'aliasname', 'password', 'email', ))
        for key, value in account_data.iteritems():
            if key not in request.cfg.user_transient_fields:
                setattr(u, key, value)
        u.valid = True
        u.create_or_update(True)
        if verbose: request.log("interwiki: successful interwiki auth for %r" % name)
        return ContinueLogin(u)


