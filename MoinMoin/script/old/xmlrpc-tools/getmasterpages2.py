#!/usr/bin/env python
"""
This script is a hack because moinmaster wiki does not support
xmlrpc due to unknown reasons. It gets all SystemPages from srcwiki
via action=raw and stores them into dstwiki via xmlrpc.

We use wiki rpc v2 here.

GPL software, 2003-09-27 Thomas Waldmann
"""

import xmlrpclib, urllib
from MoinMoin import wikiutil
from MoinMoin.support.BasicAuthTransport import BasicAuthTransport

srcurlformat = "http://moinmaster.wikiwikiweb.de/%s?action=raw"
user = "YourWikiName"
password = "yourbasicauthpassword"
srcwiki = xmlrpclib.ServerProxy("http://moinmaster.wikiwikiweb.de/?action=xmlrpc2")
dsttrans = BasicAuthTransport(user, password)
dstwiki = xmlrpclib.ServerProxy("http://devel.linuxwiki.org/moin--main/__xmlrpc/?action=xmlrpc2", transport=dsttrans)

def rawGetPage(srcurl, pagename, encoding='iso-8859-1'):
    url = srcurl % wikiutil.quoteWikinameFS(pagename.encode(encoding))
    pagedata = urllib.urlopen(url).read()
    return unicode(pagedata, encoding).encode('utf-8')

def transferpage(srcurlformat, dstwiki, pagename):
    pagedata = srcwiki.getPage(pagename)
    #pagedata = rawGetPage(srcurlformat, pagename, 'iso-8859-1')
    rc = dstwiki.putPage(pagename, pagedata)
    print "Transferred %s. Len = %d, rc = %s" % (pagename.encode('ascii', 'replace'), len(pagedata), str(rc))

def run():
    allsystempagesgroup = 'AllSystemPagesGroup'
    transferpage(srcurlformat, dstwiki, allsystempagesgroup)
    allgrouppages = dstwiki.listLinks(allsystempagesgroup)

    for langgrouppage in allgrouppages:
        pagename = langgrouppage['name']
        transferpage(srcurlformat, dstwiki, pagename)
        pages = dstwiki.listLinks(pagename)
        for page in pages:
            transferpage(srcurlformat, dstwiki, page['name'])

if __name__ == "__main__":
    run()

