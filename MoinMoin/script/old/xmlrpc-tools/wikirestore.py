#!/usr/bin/env python
"""
This script reads a wikibackup.pickle file and puts
all Pages contained there into a wiki via xmlrpc.
We use wiki rpc v2 here.

Important note:

This script ONLY handles the current versions of the wiki pages.

It does NOT handle:
    * event or edit logs (page history)
    * old versions of pages
    * attachments
    * user account data
    * MoinMoin code or config running the wiki

So this is definitely NOT a complete restore.

GPL software, 2003-10-24 Thomas Waldmann
"""
def run():
    import xmlrpclib
    from MoinMoin.support.BasicAuthTransport import BasicAuthTransport
    from MoinMoin.util import pickle

    user = "ThomasWaldmann"
    password = "xxxxxxxxxxxx"
    dsttrans = BasicAuthTransport(user, password)
    dstwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/__xmlrpc/?action=xmlrpc2", transport=dsttrans)
    #dstwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/?action=xmlrpc2")

    backupfile = open("wikibackup.pickle", "r")
    backup = pickle.load(backupfile)
    backupfile.close()

    for pagename in backup:
        pagedata = backup[pagename]
        dstwiki.putPage(pagename, pagedata) # TODO: add error check
        print "Put %s." % pagename

if __name__ == "__main__":
    run()

