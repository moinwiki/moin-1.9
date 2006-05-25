# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - create a user account

    @copyright: 2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--name", metavar="NAME", dest="uname",
            help="Set the wiki user name to NAME."
        )
        self.parser.add_option(
            "--alias", metavar="ALIAS", dest="ualiasname",
            help="Set the wiki user alias name to ALIAS (e.g. the real name if NAME is cryptic)."
        )
        self.parser.add_option(
            "--email", metavar="EMAIL", dest="email",
            help="Set the user's email address to EMAIL."
        )
        self.parser.add_option(
            "--password", metavar="PASSWORD", dest="password",
            help="Set the user's password to PASSWORD (either cleartext or {SHA1}...)."
        )

    def mainloop(self):
        # we don't expect non-option arguments
        if len(self.args) != 0:
            self.parser.error("incorrect number of arguments")

        flags_given = self.options.uname and self.options.email
        if not flags_given:
            self.parser.print_help()
            import sys
            sys.exit(1)

        self.init_request()
        request = self.request

        from MoinMoin import user, wikiutil
        u = user.User(request, None, self.options.uname, password=self.options.password)
        u.email = self.options.email
        u.aliasname = self.options.ualiasname or ''
        print " %-20s %-25s %-35s" % (u.id, u.name, u.email),
        u.save()
        print "- created."

