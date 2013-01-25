# -*- coding: iso-8859-1 -*-
"""
MoinMoin - find inactive users (and disable / remove them)

@copyright: 2013 MoinMoin:ThomasWaldmann,
@license: GNU GPL, see COPYING for details.
"""

import sys, os

from MoinMoin.script import MoinScript, log
from MoinMoin.user import getUserList, User
from MoinMoin.logfile import editlog

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to find inactive users on your wiki via a command line interface.

Inactive user means: a user profile with a specific userid exists, but there is not
any edit logged for that userid.

But please review the list before removing or disabling users, there are legitimate
users who just read and never edit. If your wiki has strict ACLs, they might need
to be able to log in to read. Use --show.

Usage:
    For all your wikis sharing a single user_dir, run:
        moin ... account inactive --py-append keep-users.py
    Then, run (for one of the wikis sharing this user_dir):
        moin ... account inactive --py-exec keep-users.py --show
    If you want to keep some user profiles that are shown there, add the userids to
    the keep-users.py file in the same way as all the other userids you see there.
    Finally run the command with --disable or --remove instead of --show.

Detailed Instructions:
======================
General syntax: moin [options] account inactive [inactive-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--py-append", metavar="FILENAME", dest="py_append_file",
            help="Append python code with editlog user ids."
        )
        self.parser.add_option(
            "--py-exec", metavar="FILENAME", dest="py_exec_file",
            help="Execute python code to read editlog user ids."
        )
        self.parser.add_option(
            "--show", dest="show", action="store_true",
            help="Show all inactive users."
        )
        self.parser.add_option(
            "--disable", dest="disable", action="store_true",
            help="Disable all inactive users."
        )
        self.parser.add_option(
            "--remove", dest="remove", action="store_true",
            help="Remove all inactive users."
        )
        self.parser.add_option(
            "--interactive", dest="interactive", action="store_true",
            help="Show data and ask before deleting/disabling users."
        )

    def mainloop(self):
        argc = len(self.args)

        self.init_request()
        request = self.request

        if self.options.py_append_file:
            def logs(request):
                """ generator for log objects """
                # global edit-log
                yield editlog.EditLog(request)
                # local edit-log of every page
                for pn in request.rootpage.getPageList(exists=False):
                    yield editlog.EditLog(request, rootpagename=pn)

            def uids(log):
                """ generator for userids found in a log """
                for line in log:
                    uid = line.userid
                    if uid:
                        yield uid

            fn = self.options.py_append_file
            editlog_uids = set()
            for log in logs(request):
                editlog_uids |= set(uids(log))
            with open(fn, "a") as f:
                for uid in editlog_uids:
                    u = User(request, uid)
                    code = u'editlog_uids.add(%r)  # %r %r %r\n' % (
                               uid, u.name, u.email, u.jid)
                    f.write(code.encode('utf-8'))

        elif self.options.py_exec_file:
            def check_interactive(u):
                if self.options.interactive:
                    prompt = "%s %r %r %r disabled=%r (y/N)? " % (u.id, u.name, u.email, u.jid, u.disabled)
                    return raw_input(prompt).strip() in ['y', 'Y', ]
                else:
                    return True

            fn = self.options.py_exec_file
            locs = dict(editlog_uids=set())
            execfile(fn, {}, locs)
            editlog_uids = locs.get('editlog_uids')

            profile_uids = set(getUserList(request))

            inactive_uids = profile_uids - editlog_uids
            for uid in inactive_uids:
                u = User(request, uid)
                if self.options.show:
                    print "%s\t%r\t%r\t%r" % (uid, u.name, u.email, u.disabled)
                if self.options.disable:
                    if check_interactive(u):
                        u.disabled = 1
                        u.save()
                elif self.options.remove:
                    if check_interactive(u):
                        u.remove()

