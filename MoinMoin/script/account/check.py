# -*- coding: iso-8859-1 -*-
"""
MoinMoin - check / process user accounts

@copyright: 2003-2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

# ----------------------------------------------------------------------------
# if a user subscribes to magicpages, it means that he wants to keep
# exactly THIS account - this will avoid deleting it.
magicpages = [
    "ThisAccountIsCorrect",
    "DieserAccountIstRichtig",
]

# ----------------------------------------------------------------------------

import os, sys

from MoinMoin.script import MoinScript
from MoinMoin import user, wikiutil

class PluginScript(MoinScript):
    """\
Purpose:
========
When using ACLs, a wiki user name has to be unique, there must not be
multiple accounts having the same username. The problem is, that this
was possible before the introduction of ACLs and many users, who forgot
their ID, simply created a new ID using the same user name.

Because access rights (when using ACLs) depend on the NAME (not the ID),
this must be cleaned up before using ACLs or users will have difficulties
changing settings and saving their account data (system won't accept the
save, if the user name and email is not unique).

Detailed Instructions:
======================

General syntax: moin [options] account check [check-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[check-options] see below:

    0. Check the settings at top of the code!
       Making a backup of your wiki might be also a great idea.

    1. Best is to first look at duplicate user names:
       moin ... account check --usersunique

       If everything looks OK there, you may save that to disk:
       moin ... account check --usersunique --save

    2. Now, check also for duplicate email addresses:
       moin ... account check --emailsunique

       If everything looks OK, you may save that to disk:
       moin ... account check --emailsunique --save

    3. If the announced action is incorrect, you may choose to better manually
       disable some accounts: moin ... account disable --uid 1234567.8.90

    4. After cleaning up, do 1. and 2. again. There should be no output now, if
       everything is OK.

    5. Optionally you may want to make wikinames out of the user names
       moin ... account check --wikinames
       moin ... account check --wikinames --save
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self._addFlag("usersunique",
            "Makes user names unique (by appending the ID to"
            " name and email, disabling subscribed pages and"
            " disabling all, but the latest saved user account);"
            " default is to SHOW what will be happening, you"
            " need to give the --save option to really do it."
        )
        self._addFlag("emailsunique",
            "Makes user emails unique;"
            " default is to show, use --save to save it."
        )
        self._addFlag("wikinames",
            "Convert user account names to wikinames (camel-case)."
        )
        self._addFlag("save",
            "If specified as LAST option, will allow the other"
            " options to save user accounts back to disk."
            " If not specified, no settings will be changed permanently."
        )
        self._addFlag("removepasswords",
            "Remove pre-1.1 cleartext passwords from accounts."
        )

    def _addFlag(self, name, help):
        self.parser.add_option("--" + name,
            action="store_true", dest=name, default=0, help=help)

    def collect_data(self):
        import re
        request = self.request
        for uid in user.getUserList(request):
            u = user.User(request, uid)
            self.users[uid] = u

            # collect name duplicates:
            if u.name in self.names:
                self.names[u.name].append(uid)
            else:
                self.names[u.name] = [uid]

            # collect email duplicates:
            if u.email:
                if u.email in self.emails:
                    self.emails[u.email].append(uid)
                else:
                    self.emails[u.email] = [uid]

            # collect account with no or invalid email address set:
            if not u.email or not re.match(".*@.*\..*", u.email):
                self.uids_noemail[uid] = u.name

    def hasmagicpage(self, uid):
        u = self.users[uid]
        return u.isSubscribedTo(magicpages)

    def disableUser(self, uid):
        u = self.users[uid]
        print " %-20s %-30r %-35r" % (uid, u.name, u.email),
        keepthis = self.hasmagicpage(uid)
        if keepthis:
            print "- keeping (magicpage)!"
            u.save() # update timestamp, so this will be latest next run
        elif not u.disabled: # only disable once
            u.disabled = 1
            u.name = "%s-%s" % (u.name, uid)
            if u.email:
                u.email = "%s-%s" % (u.email, uid)
            u.subscribed_pages = "" # avoid using email
            if self.options.save:
                u.save()
                print "- disabled."
            else:
                print "- would be disabled."

    def getsortvalue(self, uid, user):
        return float(user.last_saved) # when user did last SAVE of his account data

    def process(self, uidlist):
        sortlist = []
        for uid in uidlist:
            u = self.users[uid]
            sortlist.append((self.getsortvalue(uid, u), uid))
        sortlist.sort()
        #print sortlist
        # disable all, but the last/latest one
        for dummy, uid in sortlist[:-1]:
            self.disableUser(uid)
        # show what will be kept
        uid = sortlist[-1][1]
        u = self.users[uid]
        print " %-20s %-30r %-35r - keeping%s!" % (uid, u.name, u.email, self.hasmagicpage(uid) and " (magicpage)" or "")

    def make_users_unique(self):
        for name, uids in self.names.items():
            if len(uids) > 1:
                self.process(uids)

    def make_emails_unique(self):
        for email, uids in self.emails.items():
            if len(uids) > 1:
                self.process(uids)

    def make_WikiNames(self):
        for uid, u in self.users.items():
            if u.disabled:
                continue
            if not wikiutil.isStrictWikiname(u.name):
                newname = u.name.capwords().replace(" ", "").replace("-", "")
                if not wikiutil.isStrictWikiname(newname):
                    print " %-20s %-30r - no WikiName, giving up" % (uid, u.name)
                else:
                    print " %-20s %-30r - no WikiName -> %r" % (uid, u.name, newname)
                    if self.options.save:
                        u.name = newname
                        u.save()

    def remove_passwords(self):
        for uid, u in self.users.items():
            # user.User already clears the old cleartext passwords on loading,
            # so nothing to do here!
            if self.options.save:
                # we can't encrypt the cleartext password as it is cleared
                # already. and we would not trust it anyway, so we don't WANT
                # to do that either!
                # Just save the account data without cleartext password:
                print " %-20s %-25s - saving" % (uid, u.name)
                u.save()

    def mainloop(self):
        # we don't expect non-option arguments
        if len(self.args) != 0:
            self.parser.error("incorrect number of arguments")

        # check for correct option combination
        flags_given = (self.options.usersunique
                    or self.options.emailsunique
                    or self.options.wikinames
                    or self.options.removepasswords)

        # no option given ==> show usage
        if not flags_given:
            self.parser.print_help()
            sys.exit(1)

        self.init_request()

        self.users = {} # uid : UserObject
        self.names = {} # name : [uid, uid, uid]
        self.emails = {} # email : [uid, uid, uid]
        self.uids_noemail = {} # uid : name

        self.collect_data()
        if self.options.usersunique:
            self.make_users_unique()
        if self.options.emailsunique:
            self.make_emails_unique()
        if self.options.wikinames:
            self.make_WikiNames()
        if self.options.removepasswords:
            self.remove_passwords()

