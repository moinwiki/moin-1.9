# -*- coding: iso-8859-1 -*-
"""
MoinMoin - change or reset the password of a user account

@copyright: 2006-2013 MoinMoin:ThomasWaldmann,
            2008 MoinMoin:JohannesBerg
@license: GNU GPL, see COPYING for details.
"""

from __future__ import with_statement

import sys

from MoinMoin.script import MoinScript, log
from MoinMoin.user import getUserList, set_password, Fault


class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to change a user password via a command line interface.

Detailed Instructions:
======================
General syntax: moin [options] account resetpw [newpw-options] [newpassword]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

newpassword:
    The new password, optional. If newpassword is not given, the password will
    be invalidated (and the user will not be able to log in with any password,
    so the user will need to do a password recovery).

[newpw-options] see below:
    1. To change JohnSmith's password:
       moin ... account resetpw --name JohnSmith JohnsNewSuperSecretPassword

    2. To change the password for the UID '1198872910.78.56322':
       moin ... account resetpw --uid 1198872910.78.56322 TheNewPassword

    3. To invalidate the password of all users and notify them via e-mail,
       giving verbose progress information:
       moin ... --verbose account resetpw --all-users --notify

       Please note:
       - if you have many users, this will generate many e-mails
       - if a user does not have an e-mail address in his profile, he can not
         get notified
       - disabled user profiles will get the password reset, but won't get
         notified (they can't be used any more anyway).
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
        self.parser.add_option(
            "-a", "--all-users", dest="all_users", action="store_true",
            help="Reset password for ALL users."
        )
        self.parser.add_option(
            "--notify", dest="notify", action="store_true",
            help="Notify user(s), send them an E-Mail with a password reset link."
        )
        self.parser.add_option(
            "--subject", metavar="SUBJECT", dest="subject",
            help="Subject text for the password reset notification E-Mail."
        )
        self.parser.add_option(
            "--text-intro", metavar="TEXT_INTRO", dest="text_intro",
            help="Intro text for the password reset notification E-Mail. Default: empty."
        )
        self.parser.add_option(
            "--text-msg", metavar="TEXT_MSG", dest="text_msg",
            help="Main text for the password reset notification E-Mail. Default: use the builtin standard message"
        )
        self.parser.add_option(
            "--text-data", metavar="TEXT_DATA", dest="text_data",
            help="Data template text for the password reset notification E-Mail. Default: use the builtin standard data template"
        )
        self.parser.add_option(
            "--text-from-file", metavar="TEXT_DATA", dest="text_file",
            help="Read full template for the password reset notification E-Mail from the given file, overrides --text-intro/msg/data. Default: None"
        )
        self.parser.add_option(
            "--skip-invalid", dest="skip_invalid", action="store_true",
            help="If a user's password hash is already invalid (pw is already reset), skip this user."
        )
        self.parser.add_option(
            "-v", "--verbose", dest="verbose", action="store_true",
            help="Verbose operation."
        )

    def mainloop(self):
        argc = len(self.args)
        if argc < 1:
            newpass = None
        elif argc == 1:
            newpass = self.args[0]
        else:
            self.parser.error("too many arguments given")

        flags_given = self.options.uid or self.options.uname or self.options.all_users
        if not flags_given:
            self.parser.print_help()
            sys.exit(1)

        self.init_request()
        request = self.request

        notify = self.options.notify
        if notify and not request.cfg.mail_enabled:
            print "This wiki is not enabled for mail processing. The --notify option requires this. Aborting..."
            sys.exit(1)

        skip_invalid = self.options.skip_invalid
        subject = self.options.subject
        text_intro = self.options.text_intro
        text_msg = self.options.text_msg
        text_data = self.options.text_data
        text_file = self.options.text_file

        if text_file:
            text_intro = ''
            text_msg = ''
            with open(text_file) as f:
                text_data = f.read().decode('utf-8')

        if self.options.uid:
            try:
                set_password(request, newpass, uid=self.options.uid,
                             notify=notify, skip_invalid=skip_invalid,
                             subject=subject,
                             text_intro=text_intro, text_msg=text_msg, text_data=text_data)
            except Fault, err:
                print str(err)
        elif self.options.uname:
            try:
                set_password(request, newpass, uname=self.options.uname,
                             notify=notify, skip_invalid=skip_invalid,
                             subject=subject,
                             text_intro=text_intro, text_msg=text_msg, text_data=text_data)
            except Fault, err:
                print str(err)
        elif self.options.all_users:
            uids = sorted(getUserList(request))
            total = len(uids)
            for nr, uid in enumerate(uids, start=1):
                log("%05d / %05d - processing uid %s" % (nr, total, uid))
                try:
                    set_password(request, newpass, uid=uid,
                                 notify=notify, skip_invalid=skip_invalid,
                                 subject=subject,
                                 text_intro=text_intro, text_msg=text_msg, text_data=text_data)
                except Fault, err:
                    print str(err)
