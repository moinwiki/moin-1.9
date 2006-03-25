#!/usr/bin/env python
"""
MoinMoin - check / process user accounts tool
GPL code written by Thomas Waldmann, 20031005

Why is this needed?
===================
When using ACLs, a wiki user name has to be unique, there must not be
multiple accounts having the same username. The problem is, that this
was possible before the introduction of ACLs and many users, who forgot
their ID, simply created a new ID using the same user name.

Because access rights (when using ACLs) depend on the NAME (not the ID),
this must be cleaned up before using ACLs or users will have difficulties
changing settings and saving their account data (system won't accept the
save, if the user name and email is not unique).

How to use this tool?
=====================

0. Check the settings at top of the code!
   Making a backup of your wiki might be also a great idea.
   
1. Best is to first look at duplicate user names:
    --usersunique

   If everything looks OK there, you may save that to disk:
    --usersunique --save

2. Now, check also for duplicate email addresses:
    --emailsunique

   If everything looks OK, you may save that to disk:
    --emailsunique --save

3. If the announced action is incorrect, you may choose to better manually
disable some accounts:
    --disableuser 1234567.8.90 --save

4. After cleaning up, do 1. and 2. again. There should be no output now, if
   everything is OK.
   
5. Optionally you may want to make wikinames out of the user names
    --wikinames
    --wikinames --save
    
"""

# ----------------------------------------------------------------------------
# if a user subsribes to magicpages, it means that he wants to keep
# exactly THIS account - this will avoid deleting it.
magicpages = [
    "ThisAccountIsCorrect", 
    "DieserAccountIstRichtig",
]

# ----------------------------------------------------------------------------
from MoinMoin.script import _util
config = None


#############################################################################
### Main program
#############################################################################

class MoinUserCheck(_util.Script):
    def __init__(self):
        _util.Script.__init__(self, __name__, "[options]")

        # --config=DIR
        self.parser.add_option(
            "--config", metavar="DIR", dest="configdir",
            help="Path to wikiconfig.py (or its directory)"
        )

        # --disableuser=UID
        self.parser.add_option(
            "--disableuser", metavar="UID", dest="disableuser",
            help="Disable the user with user id UID;"
                " this can't be combined with options below!"
        )

        # Flags
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
        self._addFlag("lastsaved",
            "Normally the account most recently USED will"
            " survive and the others will be disabled."
            " Using --lastsaved, the account most recently"
            " SAVED will survive."
        )
        self._addFlag("save",
            "If specified as LAST option, will allow the other"
            " options to save user accounts back to disk."
            " If not specified, no settings will be changed permanently."
        )


    def _addFlag(self, name, help):
        self.parser.add_option("--" + name,
            action="store_true", dest=name, default=0, help=help)


    def mainloop(self):
        """ moin-usercheck's main code.
        """
        import os, sys

        # we don't expect non-option arguments
        if len(self.args) != 0:
            self.parser.error("incorrect number of arguments")

        # check for correct option combination
        flags_given = (
               self.options.usersunique 
            or self.options.emailsunique 
            or self.options.wikinames)

        if flags_given and self.options.disableuser:
            # XXX: why is this? only because the former option parser code was braindead?
            self.parser.error("--disableuser can't be combined with other options!")

        # no option given ==> show usage
        if not (flags_given or self.options.disableuser):
            self.parser.print_help()
            sys.exit(1)

        #
        # Load the configuration
        #
        configdir = self.options.configdir
        if configdir:
            if os.path.isfile(configdir): configdir = os.path.dirname(configdir)
            if not os.path.isdir(configdir):
                _util.fatal("Bad path %r given to --config parameter" % configdir)
            configdir = os.path.abspath(configdir)
            sys.path[0:0] = [configdir]
            os.chdir(configdir)

        global config
        from MoinMoin import config
        if config.default_config:
            _util.fatal("You have to be in the directory containing wikiconfig.py, "
                "or use the --config option!")

        # XXX: globals bad bad bad!
        #global users, names, emails, uids_noemail
        users = {} # uid : UserObject
        names = {} # name : [uid, uid, uid]
        emails = {} # email : [uid, uid, uid]
        uids_noemail = {} # uid : name

        # XXX: Refactor to methods!
        from MoinMoin import user, wikiutil

        def collect_data():
            import re

            for uid in user.getUserList():
                u = user.User(None, uid)
                users[uid] = u
        
                # collect name duplicates:
                if names.has_key(u.name):
                    names[u.name].append(uid)
                else:
                    names[u.name] = [uid]
        
                # collect email duplicates:
                if u.email:
                    if emails.has_key(u.email):
                        emails[u.email].append(uid)
                    else:
                        emails[u.email] = [uid]
        
                # collect account with no or invalid email address set:
                if not u.email or not re.match(".*@.*\..*", u.email):
                    uids_noemail[uid] = u.name
        
        
        def hasmagicpage(uid):
            u = users[uid]
            return u.isSubscribedTo(magicpages)
        
        
        def disableUser(uid):
            u = users[uid]
            print " %-20s %-25s %-35s" % (uid, u.name, u.email),
            keepthis = hasmagicpage(uid)
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
        
        
        def getsortvalue(uid,user):
            t_ls = float(user.last_saved) # when user did last SAVE of his account data
            if self.options.lastsaved:
                return t_ls
            else: # last USED (we check the page trail for that)
                try:
                    t_lu = float(os.path.getmtime(os.path.join(config.user_dir, uid+".trail")))
                except OSError:
                    t_lu = t_ls # better than having nothing
                return t_lu
        
        
        def process(uidlist):
            sortlist = []
            for uid in uidlist:
                u = users[uid]
                sortlist.append((getsortvalue(uid,u),uid))
            sortlist.sort()
            #print sortlist
            # disable all, but the last/latest one
            for t,uid in sortlist[:-1]:
                disableUser(uid)
            # show what will be kept
            uid = sortlist[-1][1]
            u = users[uid]
            print " %-20s %-25s %-35s - keeping%s!" % (uid, u.name, u.email, hasmagicpage(uid) and " (magicpage)" or "")
        
        
        def make_users_unique():
            for name in names.keys():
                if len(names[name])>1:
                    process(names[name])
        
        
        def make_emails_unique():
            for email in emails.keys():
                if len(emails[email])>1:
                    process(emails[email])
        
        
        def make_WikiNames():
            import string
            for uid in users.keys():
                u = users[uid]
                if u.disabled: continue
                if not wikiutil.isStrictWikiname(u.name):
                    newname = string.capwords(u.name).replace(" ","").replace("-","")
                    if not wikiutil.isStrictWikiname(newname):
                        print " %-20s %-25s - no WikiName, giving up" % (uid, u.name)
                    else:
                        print " %-20s %-25s - no WikiName -> %s" % (uid, u.name, newname)
                        if self.options.save:
                            u.name = newname
                            u.save()

        collect_data()
        if self.options.disableuser:
            disableUser(self.options.disableuser)
        else:
            if self.options.usersunique:
                make_users_unique()
            if self.options.emailsunique: 
                make_emails_unique()
            if self.options.wikinames:
                make_WikiNames()


def run():
    MoinUserCheck().run()

if __name__ == "__main__":
    run()
