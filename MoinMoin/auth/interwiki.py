# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - authentication using a remote wiki

    @copyright: 2005 by Florian Festi,
                2007-2008 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import xmlrpclib

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil, user
from MoinMoin.auth import BaseAuth, ContinueLogin, CancelLogin

class InterwikiAuth(BaseAuth):
    name = 'interwiki'
    logout_possible = True
    login_inputs = ['username', 'password']

    def __init__(self, trusted_wikis, autocreate=False):
        BaseAuth.__init__(self)
        self.trusted_wikis = trusted_wikis
        self.autocreate = autocreate

    def login(self, request, user_obj, **kw):
        username = kw.get('username')
        password = kw.get('password')

        if not username or not password:
            return ContinueLogin(user_obj)

        logging.debug("trying to authenticate %r" % username)
        wikiname, username = username.split(' ', 1) # XXX Hack because ':' is not allowed in name field
        wikitag, wikiurl, name, err = wikiutil.resolve_interwiki(request, wikiname, username)

        logging.debug("resolve wiki returned: %r %r %r %r" % (wikitag, wikiurl, name, err))
        if err or wikitag not in self.trusted_wikis:
            return ContinueLogin(user_obj)

        homewiki = xmlrpclib.ServerProxy(wikiurl + "?action=xmlrpc2")
        auth_token = homewiki.getAuthToken(name, password)
        if not auth_token:
            logging.debug("%r wiki did not return an auth token." % wikitag)
            return ContinueLogin(user_obj)

        logging.debug("successfully got an auth token for %r. trying to get user profile data..." % name)

        mc = xmlrpclib.MultiCall(homewiki)
        mc.applyAuthToken(auth_token)
        mc.getUserProfile()
        result, account_data = mc()

        if result != "SUCCESS":
            logging.debug("%r wiki did not accept auth token." % wikitag)
            return ContinueLogin(None)

        if not account_data:
            logging.debug("%r wiki did not return a user profile." % wikitag)
            return ContinueLogin(None)

        logging.debug("%r wiki returned a user profile." % wikitag)

        # TODO: check remote auth_attribs
        u = user.User(request, name=name, auth_method=self.name, auth_attribs=('name', 'aliasname', 'password', 'email', ))
        for key, value in account_data.iteritems():
            if key not in request.cfg.user_transient_fields:
                setattr(u, key, value)
        u.valid = True
        if self.autocreate:
            u.create_or_update(True)
        logging.debug("successful interwiki auth for %r" % name)
        return ContinueLogin(u)

