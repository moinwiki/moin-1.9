# -*- coding: iso-8859-1 -*-
"""
MoinMoin - create a user account

@copyright: 2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to create user accounts via a command line interface.

Detailed Instructions:
======================
General syntax: moin [options] account create [create-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[create-options] see below:
    1. Verify that you have specified the right options.
       This script does no verification of email addresses or the like.

    2. To create a normal user 'JohnSmith' with an alias of 'JSmith' and an
       email of 'john@smith.com'
       moin ... account create --name JohnSmith --alias JSmith --email john@smith.com
"""

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
            help="Set the user's password to PASSWORD."
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

        from MoinMoin import user
        if user.User(request, name=self.options.uname).exists():
            print 'This username "%s" exists already!' % self.options.uname
            return
        # Email should be unique - see also MoinMoin.action.newaccount
        if self.options.email and request.cfg.user_email_unique:
            if user.get_by_email_address(request, self.options.email):
                print 'This emailaddress "%s" belongs to someone else!' % self.options.email
                return
        u = user.User(request, None, self.options.uname, password=self.options.password)
        u.email = self.options.email
        u.aliasname = self.options.ualiasname or ''
        print " %-20s %-25s %-35s" % (u.id, u.name, u.email),
        u.save()
        print "- created."
