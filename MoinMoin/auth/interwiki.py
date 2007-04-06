# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - authentication using a remote wiki

    @copyright: 2005 by Florian Festi,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import xmlrpclib
from MoinMoin import auth, wikiutil, user

def interwiki(request, **kw):
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    user_obj = kw.get('user_obj')

    if login:
        wikitag, wikiurl, wikitail, err = wikiutil.resolve_wiki(username)

        if err or wikitag not in request.cfg.trusted_wikis:
            return user_obj, True

        if password:
            homewiki = xmlrpclib.Server(wikiurl + "?action=xmlrpc2")
            account_data = homewiki.getUser(wikitail, password)
            if isinstance(account_data, str):
                # e.g. "Authentication failed", TODO: show error message
                return user_obj, True

            # TODO: check auth_attribs items
            u = user.User(request, name=username, auth_method='interwiki', auth_attribs=('name', 'aliasname', 'password', 'email', ))
            for key, value in account_data.iteritems():
                if key not in request.cfg.user_transient_fields:
                    setattr(u, key, value)
            if u:
                u.create_or_update(True)
            return u, True # moin_session has to set the cookie

    return user_obj, True
