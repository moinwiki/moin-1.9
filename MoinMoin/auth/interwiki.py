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

def interwiki(request, **kw):
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    user_obj = kw.get('user_obj')

    if login:
        if verbose: request.log("interwiki auth: trying to auth %r" % username)
        username = username.replace(' ', ':', 1) # Hack because ':' is not allowed in name field
        wikitag, wikiurl, name, err = wikiutil.resolve_wiki(request, username)

        if verbose: request.log("interwiki auth: resolve wiki returned: %r %r %r %r" % (wikitag, wikiurl, name, err))
        if err or wikitag not in request.cfg.trusted_wikis:
            return user_obj, True

        if password:
            homewiki = xmlrpclib.Server(wikiurl + "?action=xmlrpc2")
            account_data = homewiki.getUser(name, password)
            if isinstance(account_data, str):
                # e.g. "Authentication failed", TODO: show error message
                if verbose: request.log("interwiki auth: %r wiki said: %s" % (wikitag, account_data))
                return user_obj, True

            # TODO: check auth_attribs items
            u = user.User(request, name=name, auth_method='interwiki', auth_attribs=('name', 'aliasname', 'password', 'email', ))
            for key, value in account_data.iteritems():
                if key not in request.cfg.user_transient_fields:
                    setattr(u, key, value)
            u.valid = 1
            u.create_or_update(True)
            if verbose: request.log("interwiki: successful auth for %r" % name)
            return u, True # moin_session has to set the cookie

    return user_obj, True
