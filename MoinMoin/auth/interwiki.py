# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - authentication using a remote wiki

    This is completely untested and rather has to be seen as an idea
    than a working implementation.

    @copyright: 2005 by ???
    @license: GNU GPL, see COPYING for details.
"""
import xmlrpclib
from MoinMoin import auth, wikiutil, user

def interwiki(request, **kw):
    # TODO use auth_method and auth_attribs for User object
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')

    if login:
        wikitag, wikiurl, wikitail, err = wikiutil.resolve_wiki(username)

        if err or wikitag not in request.cfg.trusted_wikis:
            return user_obj, True

        if password:
            homewiki = xmlrpclib.Server(wikiurl + "?action=xmlrpc2")
            account_data = homewiki.getUser(wikitail, password)
            if isinstance(account_data, str):
                # show error message
                return user_obj, True

            u = user.User(request, name=username)
            for key, value in account_data.iteritems():
                if key not in ["may", "id", "valid", "trusted"
                               "auth_username",
                               "name", "aliasname",
                               "enc_passwd"]:
                    setattr(u, key, value)
            u.save()
            auth.setSessionCookie(request, u)
            return u, True
        else:
            pass
            # XXX redirect to homewiki

    return user_obj, True

