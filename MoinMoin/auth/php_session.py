# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PHP session cookie authentication

    Currently supported systems:

        * eGroupware 1.2 ("egw")
         * You need to configure eGroupware in the "header setup" to use
           "php sessions plus restore"

    @copyright: 2005 MoinMoin:AlexanderSchremmer (Thanks to Spreadshirt)
    @license: GNU GPL, see COPYING for details.
"""

import urllib
from MoinMoin import user
from MoinMoin.auth import _PHPsessionParser, BaseAuth

class PHPSessionAuth(BaseAuth):
    """ PHP session cookie authentication """

    name = 'php_session'

    def __init__(self, apps=['egw'], s_path="/tmp", s_prefix="sess_", autocreate=False):
        """ @param apps: A list of the enabled applications. See above for
            possible keys.
            @param s_path: The path where the PHP sessions are stored.
            @param s_prefix: The prefix of the session files.
        """
        BaseAuth.__init__(self)
        self.s_path = s_path
        self.s_prefix = s_prefix
        self.apps = apps
        self.autocreate = autocreate

    def request(self, request, user_obj, **kw):
        def handle_egroupware(session):
            """ Extracts name, fullname and email from the session. """
            username = session['egw_session']['session_lid'].split("@", 1)[0]
            known_accounts = session['egw_info_cache']['accounts']['cache']['account_data']

            # if the next line breaks, then the cache was not filled with the current
            # user information
            user_info = [value for key, value in known_accounts.items()
                         if value['account_lid'] == username][0]
            name = user_info.get('fullname', '')
            email = user_info.get('email', '')

            dec = lambda x: x and x.decode("iso-8859-1")

            return dec(username), dec(email), dec(name)

        cookie = kw.get('cookie')
        if not cookie is None:
            for cookiename in cookie:
                cookievalue = urllib.unquote(cookie[cookiename].value).decode('iso-8859-1')
                session = _PHPsessionParser.loadSession(cookievalue, path=self.s_path, prefix=self.s_prefix)
                if session:
                    if "egw" in self.apps and session.get('egw_session', None):
                        username, email, name = handle_egroupware(session)
                        break
            else:
                return user_obj, True

            u = user.User(request, name=username, auth_username=username,
                          auth_method=self.name)

            changed = False
            if name != u.aliasname:
                u.aliasname = name
                changed = True
            if email != u.email:
                u.email = email
                changed = True

            if u and self.autocreate:
                u.create_or_update(changed)
            if u and u.valid:
                return u, True # True to get other methods called, too
        return user_obj, True # continue with next method in auth list

