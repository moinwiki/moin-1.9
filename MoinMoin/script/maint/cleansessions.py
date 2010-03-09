# -*- coding: iso-8859-1 -*-
"""
MoinMoin - cleansessions script

@copyright: 2009 MoinMoin:ReimarBauer,
            2010 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

import os, time

from MoinMoin import user
from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This script allows you to clean up session files (usually used to maintain
a "logged-in session" for http(s) or xmlrpc).

Detailed Instructions:
======================
General syntax: moin [options] maint cleansessions [cleansessions-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[cleansessions-options] see below:
    --name     remove sessions only for user NAME (default: all users)
    --all      remove all sessions (default: remove outdated sessions)
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

        self.parser.add_option(
            "--name", metavar="NAME", dest="username",
            help="remove sessions only for user NAME (default: all users)"
        )
        self.parser.add_option(
            "--all", action="store_true", dest="all_sessions",
            help="remove all sessions (default: remove outdated sessions)"
        )

    def mainloop(self):
        self.init_request()
        request = self.request
        checks = []

        if not self.options.all_sessions:
            now = time.time()
            def session_expired(session):
                try:
                    return session['expires'] < now
                except KeyError:
                    # this is likely a pre-1.9.1 session file without expiry
                    return True # consider it expired
            checks.append(session_expired)

        if self.options.username:
            u = user.User(request, None, self.options.username)
            if not u.exists():
                print 'User "%s" does not exist!' % self.options.username
                return
            else:
                def user_matches(session):
                    try:
                        return session['user.id'] == u.id
                    except KeyError:
                        return False
                checks.append(user_matches)

        session_service = request.cfg.session_service
        for sid in session_service.get_all_session_ids(request):
            session = session_service.get_session(request, sid)

            # if ALL conditions are met, the session will be destroyed
            killit = True
            for check in checks:
                killit = killit and check(session)

            if killit:
                session_service.destroy_session(request, session)

