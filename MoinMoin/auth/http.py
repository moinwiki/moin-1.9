# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - http authentication

    HTTPAuth
    ========

    HTTPAuth is just a dummy redirecting to MoinMoin.auth.GivenAuth for backwards
    compatibility.

    Please fix your setup, this dummy will be removed soon:

    Old (1.8.x):
    ------------
    from MoinMoin.auth.http import HTTPAuth
    auth = [HTTPAuth(autocreate=True)]
    # any presence (or absence) of 'http' auth name, e.g.:
    auth_methods_trusted = ['http', 'xmlrpc_applytoken']

    New (1.9.x):
    ------------
    from MoinMoin.auth import GivenAuth
    auth = [GivenAuth(autocreate=True)]
    # presence (or absence) of 'given' auth name, e.g.:
    auth_methods_trusted = ['given', 'xmlrpc_applytoken']

    HTTPAuthMoin
    ============

    HTTPAuthMoin is HTTP auth done by moin (not by your web server).

    Moin will request HTTP Basic Auth and use the HTTP Basic Auth header it
    receives to authenticate username/password against the moin user profiles.

    from MoinMoin.auth.http import HTTPAuthMoin
    auth = [HTTPAuthMoin()]
    # check if you want 'http' auth name in there:
    auth_methods_trusted = ['http', 'xmlrpc_applytoken']

    @copyright: 2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, user
from MoinMoin.auth import BaseAuth, GivenAuth


class HTTPAuth(GivenAuth):
    name = 'http'  # GivenAuth uses 'given'
    logging.warning("DEPRECATED use of MoinMoin.auth.http.HTTPAuth, please read instructions there or docs/CHANGES!")


class HTTPAuthMoin(BaseAuth):
    """ authenticate via http (basic) auth """
    name = 'http'

    def __init__(self, autocreate=False, realm='MoinMoin', coding='iso-8859-1'):
        self.autocreate = autocreate
        self.realm = realm
        self.coding = coding
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

        auth = request.authorization
        if auth and auth.username and auth.password is not None:
            logging.debug("http basic auth, received username: %r password: %r" % (
                          auth.username, auth.password))
            u = user.User(request,
                          name=auth.username.decode(self.coding),
                          password=auth.password.decode(self.coding),
                          auth_method=self.name, auth_attribs=[])
            logging.debug("user: %r" % u)

        if not u or not u.valid:
            from werkzeug import Response, abort
            response = Response(_('Please log in first.'), 401,
                                {'WWW-Authenticate': 'Basic realm="%s"' % self.realm})
            abort(response)

        logging.debug("u: %r" % u)
        if u and self.autocreate:
            logging.debug("autocreating user")
            u.create_or_update()
        if u and u.valid:
            logging.debug("returning valid user %r" % u)
            return u, True # True to get other methods called, too
        else:
            logging.debug("returning %r" % user_obj)
            return user_obj, True

