#!/usr/bin/env python
"""
This script gets all Pages from a wiki via xmlrpc and
stores them into a backup file. We use wiki rpc v2 here.

Important note:

This script ONLY handles the current versions of the wiki pages.

It does NOT handle:
    * event or edit logs (page history)
    * old versions of pages
    * attachments
    * user account data
    * MoinMoin code or config running the wiki

So this is definitely NOT a complete backup.

GPL software, 2003-08-10 Thomas Waldmann
"""
def run():
    import xmlrpclib
    from MoinMoin.support.BasicAuthTransport import BasicAuthTransport
    from MoinMoin.util import pickle, PICKLE_PROTOCOL

    #user = "username"
    #password = "xxxxxxxx"
    #srctrans = BasicAuthTransport(user,password)
    #srcwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/__xmlrpc/?action=xmlrpc2", transport=srctrans)
    srcwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/?action=xmlrpc2")

    backup = {}
    allpages = srcwiki.getAllPages()
    for pagename in allpages:
        pagedata = srcwiki.getPage(pagename)
        print "Got %s." % pagename
        backup[pagename] = pagedata

    backupfile = open("wikibackup.pickle", "w")
    pickle.dump(backup, backupfile, PICKLE_PROTOCOL)
    backupfile.close()

if __name__ == "__main__":
    run()

