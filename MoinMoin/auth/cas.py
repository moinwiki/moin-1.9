# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CAS authentication

    Jasig CAS (see http://www.jasig.org/cas) authentication module.

    @copyright: 2009 MoinMoin:RichardLiao
    @license: GNU GPL, see COPYING for details.
"""

import time, re
import urlparse
import urllib, urllib2

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.auth import BaseAuth
from MoinMoin import user, wikiutil


class PyCAS(object):
    """A class for working with a CAS server."""

    def __init__(self, server_url, renew=False, login_path='/login', logout_path='/logout',
                 validate_path='/validate', coding='utf-8'):
        self.server_url = server_url
        self.renew = renew
        self.login_path = login_path
        self.logout_path = logout_path
        self.validate_path = validate_path
        self.coding = coding

    def login_url(self, service):
        """Return the login URL for the given service."""
        url = self.server_url + self.login_path + '?service=' + urllib.quote_plus(service)
        if self.renew:
            url += "&renew=true"
        return url

    def logout_url(self, redirect_url=None):
        """Return the logout URL."""
        url = self.server_url + self.logout_path
        if redirect_url:
            url += '?url=' + urllib.quote_plus(redirect_url)
        return url

    def validate_url(self, service, ticket):
        """Return the validation URL for the given service. (For CAS 1.0)"""
        url = self.server_url + self.validate_path + '?service=' + urllib.quote_plus(service) + '&ticket=' + urllib.quote_plus(ticket)
        if self.renew:
            url += "&renew=true"
        return url

    def validate_ticket(self, service, ticket):
        """Validate the given ticket against the given service."""
        f = urllib2.urlopen(self.validate_url(service, ticket))
        valid = f.readline()
        valid = valid.strip() == 'yes'
        user = f.readline().strip()
        user = user.decode(self.coding)
        return valid, user


class CASAuth(BaseAuth):
    """ handle login from CAS """
    name = 'CAS'
    login_inputs = ['username', 'password']
    logout_possible = True

    def __init__(self, auth_server, login_path="/login", logout_path="/logout", validate_path="/validate"):
        BaseAuth.__init__(self)
        self.cas = PyCAS(auth_server, login_path=login_path,
                         validate_path=validate_path, logout_path=logout_path)

    def request(self, request, user_obj, **kw):
        ticket = request.args.get('ticket')
        action = request.args.get("action", [])
        logoutRequest = request.args.get('logoutRequest', [])
        url = request.getBaseURL() + urllib.quote_plus(request.getPathinfo().encode('utf-8'))

        # # handle logout request from CAS
        # if logoutRequest:
            # logoutRequestMatch = re.search("<samlp:SessionIndex>(.*)</samlp:SessionIndex>", logoutRequest[0])
            # service_ticket = logoutRequestMatch.group(1)
            # if service_ticket:
                # # TODO: logout
                # return self.logout(request, user_obj)

        # authenticated user
        if user_obj and user_obj.valid:
            return user_obj, True

        # anonymous
        if not ticket and not "login" in action:
            return user_obj, True

        # valid ticket on CAS
        if ticket:
            valid, username = self.cas.validate_ticket(url, ticket[0])
            if valid:
                u = user.User(request, auth_username=username, auth_method=self.name)
                u.valid = valid
                # auto create user
                u.create_or_update(True)
                return u, True

        # login
        request.http_redirect(self.cas.login_url(url))

        return user_obj, True

    def logout(self, request, user_obj, **kw):
        if self.name and user_obj and user_obj.auth_method == self.name:
            url = request.getBaseURL() + urllib.quote_plus(request.getPathinfo().encode('utf-8'))
            request.http_redirect(self.cas.logout_url(url))

            user_obj.valid = False

        return user_obj, True

