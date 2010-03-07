# -*- coding: iso-8859-1 -*-
"""
MoinMoin - disable a user account

@copyright: 2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to disable user accounts via a command line interface.

Detailed Instructions:
======================
General syntax: moin [options] account disable [disable-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[disable-options] see below:
    0. Verify that you really want to disable the account.
       While there is a disable script, no such enable script exists.

    1. To disable the user 'JohnSmith':
       moin ... account disable --name JohnSmith

    2. To disable the user 'JohnSmith', based on his UID '1198872910.78.56322':
       moin ... account disable --uid 1198872910.78.56322
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--uid", metavar="UID", dest="uid",
            help="Disable the user with user id UID."
        )
        self.parser.add_option(
            "--name", metavar="NAME", dest="uname",
            help="Disable the user with user name NAME."
        )

    def mainloop(self):
        # we don't expect non-option arguments
        if len(self.args) != 0:
            self.parser.error("incorrect number of arguments")

        flags_given = self.options.uid or self.options.uname
        if not flags_given:
            self.parser.print_help()
            import sys
            sys.exit(1)

        self.init_request()
        request = self.request

        from MoinMoin import user
        if self.options.uid:
            u = user.User(request, self.options.uid)
        elif self.options.uname:
            u = user.User(request, None, self.options.uname)

        if not u.exists():
            print 'This user "%s" does not exists!' % u.name
            return

        print " %-20s %-25s %-35s" % (u.id, u.name, u.email),
        if not u.disabled: # only disable once
            u.disabled = 1
            u.name = "%s-%s" % (u.name, u.id)
            if u.email:
                u.email = "%s-%s" % (u.email, u.id)
            u.subscribed_pages = "" # avoid using email
            u.save()
            print "- disabled."
        else:
            print "- is already disabled."
