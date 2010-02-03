#!/usr/bin/env python
"""
This script checks whether the wiki authenticates and trusts you.

It calls the TrustMe.py xmlrpc plugin. To use http auth, you need to configure
the srcwiki with auth = [http, moin_cookie] in its wikiconfig.

GPL software, 2005 Thomas Waldmann
"""

def run():
    user = "ThomasWaldmann"
    password = "wrong"

    import sys, xmlrpclib
    sys.path.insert(0, '../../..')
    from MoinMoin.support.BasicAuthTransport import BasicAuthTransport

    srctrans = BasicAuthTransport(user, password)
    srcwiki = xmlrpclib.ServerProxy("http://master.moinmo.in/?action=xmlrpc2", transport=srctrans)

    print srcwiki.WhoAmI()

if __name__ == "__main__":
    run()

