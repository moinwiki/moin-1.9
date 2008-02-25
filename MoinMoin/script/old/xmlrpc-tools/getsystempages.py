#!/usr/bin/env python
"""
This script gets all SystemPages from srcwiki via xmlrpc and
stores them into dstwiki via xmlrpc. We use wiki rpc v1 here.

*** DO NOT USE, SEE getsystempages2.py ***

GPL software, 2003-08-10 Thomas Waldmann
"""

from xmlrpclib import *

srcwiki = ServerProxy("http://master.moinmo.in/?action=xmlrpc")
#srcwiki = ServerProxy("http://master.moinmo.in/?action=xmlrpc")
dstwiki = ServerProxy("http://devel.linuxwiki.org/moin--cvs?action=xmlrpc")

def transferpage(srcwiki, dstwiki, pagename):
    pagedata = srcwiki.getPage(pagename).data
    dstwiki.putPage(pagename, Binary(pagedata))
    print "Transferred %s." % pagename

def run():
    allsystempagesgroup = 'AllSystemPagesGroup'
    transferpage(srcwiki, dstwiki, allsystempagesgroup)
    allgrouppages = srcwiki.listLinks(allsystempagesgroup)
    for langgrouppage in allgrouppages:
        pagename = langgrouppage['name']
        transferpage(srcwiki, dstwiki, pagename)
        pages = srcwiki.listLinks(pagename)
        for page in pages:
            transferpage(srcwiki, dstwiki, page['name'])

if __name__ == "__main__":
    run()

