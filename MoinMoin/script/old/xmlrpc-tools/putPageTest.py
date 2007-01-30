#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script is just an example how to put data into a wiki using xmlrpc.
We use wiki rpc v2 here.

This script only works if you edited MoinMoin/xmlrpc/__init__.py (see the
comment in the putPage handler) to not require http auth (trusted user) and to
really use the pagename we give.

This can be done for migrating data into an offline moin wiki running on
localhost - don't put a wiki configured like this on the internet!

GPL software, 2005 Thomas Waldmann
"""
def run():
    import xmlrpclib
    mywiki = xmlrpclib.ServerProxy("http://localhost/mywiki/?action=xmlrpc2")

    # first a simple test in pure ascii
    pagename = "ApureAsciiPage"
    pagedata = "My first test."
    mywiki.putPage(pagename, pagedata)

    # now let's use some utf-8 encoded pagename and text
    # this stuff will only look correct if you use utf-8 enabled equipment.
    pagename = "SomeUtf8Pagename-äöüÄÖÜß¢" # we use some german chars here
    pagedata = "Some UTF-8 content: äöü ÄÖÜ ß ¢"
    mywiki.putPage(pagename, pagedata)

    # if you have data in iso-8859-1 (latin1) encoding, then use code similar to:
    # pagename = latin1pagename.decode('iso-8859-1').encode('utf-8')
    # pagedata = latin1pagedata.decode('iso-8859-1').encode('utf-8')
    # mywiki.putPage(pagename, pagedata)

if __name__ == "__main__":
    run()

