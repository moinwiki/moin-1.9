#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
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

import sys, re

# ----------------------------------------------------------------------------
# CHECK THESE SETTINGS, then remove or comment out the following line:
#print "Check the settings in the script first, please!" ; sys.exit(1)

# this is where your moinmoin code is (if you installed it using
# setup.py into your python site-packages, then you don't need that setting):
sys.path.insert(0, '/home/twaldmann/moincvs/moin--main')

# this is where your wikiconfig.py is:
sys.path.insert(0, '/org/org.linuxwiki/cgi-bin')

# if you include other stuff in your wikiconfig, you might need additional
# pathes in your search path. Put them here:
sys.path.insert(0, '/org/wiki')

# if a user subsribes to magicpage, it means that he wants to keep
# exactly THIS account - this will avoid deleting it.
#magicpage = "ThisAccountIsCorrect"
magicpage = "DieserAccountIstRichtig"

# ----------------------------------------------------------------------------

from MoinMoin.user import *
from MoinMoin import config, wikiutil

def collect_data():
    for uid in getUserList(request): # XXX FIXME make request object for getting config vars there
        u = User(None, uid)
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
    return u.subscribed_pages.find(magicpage) >= 0

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
        if save:
            u.save()
            print "- disabled."
        else:
            print "- would be disabled."

def getsortvalue(uid,user):
    t_ls = float(user.last_saved) # when user did last SAVE of his account data
    if lastsaved:
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
                if save:
                    u.name = newname
                    u.save()
            
def do_removepasswords():
    for uid in users.keys():
        u = users[uid]
        # user.User already clears the old cleartext passwords on loading,
        # so nothing to do here!
        if save:
            # we can't encrypt the cleartext password as it is cleared
            # already. and we would not trust it anyway, so we don't WANT
            # to do that either!
            # Just save the account data without cleartext password:
            print " %-20s %-25s - saving" % (uid, u.name)
            u.save()
            
# here the main routine starts --------------------------------
usersunique = emailsunique = lastsaved = save = 0
disableuser = wikinames = removepasswords = 0

users = {} # uid : UserObject
names = {} # name : [uid, uid, uid]
emails = {} # email : [uid, uid, uid]
uids_noemail = {} # uid : name

def run():
    global usersunique, emailsunique, lastsaved, save, disableuser, wikinames
    global users, names, emails, uids_noemail, removepasswords
    
    if "--usersunique" in sys.argv:  usersunique = 1
    if "--emailsunique" in sys.argv: emailsunique = 1
    if "--lastsaved" in sys.argv:    lastsaved = 1
    if "--wikinames" in sys.argv:    wikinames = 1
    if "--removepasswords" in sys.argv:    removepasswords = 1
    if "--save" in sys.argv:         save = 1

    if "--disableuser" in sys.argv:  disableuser = 1

    if not usersunique and not emailsunique and not disableuser and \
       not wikinames and not removepasswords:
        print """%s
    Options:
        --usersunique       makes user names unique (by appending the ID to
                            name and email, disabling subscribed pages and
                            disabling all, but the latest saved user account)
                            default is to SHOW what will be happening, you
                            need to give the --save option to really do it.

        --emailsunique      makes user emails unique
                            default is to show, use --save to save it.

        --lastsaved         normally the account most recently USED will
                            survive and the others will be disabled.
                            using --lastsaved, the account most recently
                            SAVED will survive.

        --disableuser uid   disable the user with user id uid
                            this can't be combined with the options above!
                            
        --wikinames         try to make "WikiNames" out of "user names"
        --removepasswords   remove pre-1.1 cleartext passwords from accounts
        
        --save              if specified as LAST option, will allow the other
                            options to save user accounts back to disk.
                            if not specified, no settings will be permanently
                            changed.

    """ % sys.argv[0]
        return
        
    collect_data()
    if usersunique:  make_users_unique()
    if emailsunique: make_emails_unique()
    if disableuser:  disableUser(sys.argv[2])
    if wikinames:    make_WikiNames()
    if removepasswords: do_removepasswords()

if __name__ == "__main__":
    run()

# EOF

