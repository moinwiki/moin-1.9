# -*- coding: iso-8859-1 -*-
"""
MoinMoin - disable a user account

@copyright: 2006 MoinMoin:ThomasWaldmann,
            2008 MoinMoin:JohannesBerg
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to change a user password via a command line interface.

Detailed Instructions:
======================
General syntax: moin [options] account resetpw [newpw-options] newpassword

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[newpw-options] see below:
    1. To change JohnSmith's password:
       moin ... account resetpw --name JohnSmith new-password

    2. To change the password for the UID '1198872910.78.56322':
       moin ... account resetpw --uid 1198872910.78.56322 new-password
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--uid", metavar="UID", dest="uid",
            help="Reset password for the user with user id UID."
        )
        self.parser.add_option(
            "--name", metavar="NAME", dest="uname",
            help="Reset password for the user with user name NAME."
        )

    def mainloop(self):
        # we don't expect non-option arguments
        if len(self.args) != 1:
            self.parser.error("no new password given")
        newpass = self.args[0]

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

        u.enc_password = user.encodePassword(newpass)
        u.save()
