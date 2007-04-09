#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This script is just an example how to update a group definition page using xmlrpc.

GPL software, 2005 Thomas Waldmann
"""
def run():
    import sys
    sys.path.insert(0, '../../..')

    import xmlrpclib
    from MoinMoin.support.BasicAuthTransport import BasicAuthTransport

    user = "XmlRpc"
    password = "wrong"
    dsttrans = BasicAuthTransport(user, password)
    mywiki = xmlrpclib.ServerProxy("http://enterprise.wikiwikiweb.de:8888/?action=xmlrpc2", transport=dsttrans)

    groupname = "TestGroup"
    groupdesc = "This is just a test."
    groupmembers = ["TestUser1", "TestUser2",]
    print mywiki.UpdateGroup(groupname, groupdesc, groupmembers)

    groupname = "TestAclGroup"
    groupdesc = "This is just a test."
    groupmembers = ["TestUser3",]
    print mywiki.UpdateGroup(groupname, groupdesc, groupmembers, "All:read,write,delete,revert")

    del mywiki
    del dsttrans

    user = "XmlRpc"
    password = "completelywrong"
    dsttrans = BasicAuthTransport(user, password)
    mywiki = xmlrpclib.ServerProxy("http://enterprise.wikiwikiweb.de:8888/?action=xmlrpc2", transport=dsttrans)

    groupname = "TestGroup"
    groupdesc = "This is just a test."
    groupmembers = ["WrongUser1", "WrongUser2",]
    print mywiki.UpdateGroup(groupname, groupdesc, groupmembers)


if __name__ == "__main__":
    run()

