#!/usr/bin/env python
"""
This script gets all SystemPages from srcwiki via xmlrpc and
stores them into dstwiki via xmlrpc. We use wiki rpc v2 here.

GPL software, 2003-08-10 Thomas Waldmann
"""

import xmlrpclib
from MoinMoin.support.BasicAuthTransport import BasicAuthTransport

#srcwiki = xmlrpclib.ServerProxy("http://moinmaster.wikiwikiweb.de/FrontPage?action=xmlrpc")
user = "YourWikiName"
password = "yourbasicauthpassword"
srctrans = BasicAuthTransport(user,password)
dsttrans = BasicAuthTransport(user,password)
srcwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/__xmlrpc/?action=xmlrpc2", transport=srctrans)
dstwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--cvs/__xmlrpc/?action=xmlrpc2", transport=dsttrans)

def transferpage(srcwiki, dstwiki, pagename):
    pagedata = srcwiki.getPage(pagename)
    dstwiki.putPage(pagename, pagedata)
    print "Transferred %s." % pagename.encode('ascii', 'replace')

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

