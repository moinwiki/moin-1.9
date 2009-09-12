#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - client side of xmlrpc UpdateGroup functionality.

    You can use this code to update a group page in a target wiki via xmlrpc.
    Of course you need to enable the xmlrpc service in the target wiki, see
    your actions_excluded settings (by default, it contains 'xmlrpc')!

    @copyright: 2006-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
# convenience: fixup python path so script can be started from here:
import sys
sys.path.insert(0, '../../../..')

import xmlrpclib


def updateGroup(server_url, username, password, groupname, groupdesc, groupmembers, acl=''):
    """
    Update a Wiki Group Page named <groupname> with a list of <groupmembers> via xmlrpc.
    Contact the target wiki xmlrpc service at <server_url> and use <username>
    and <password> to authenticate as wiki user there.

    @param server_url: xmlrpc service url of target wiki (str)
    @param username: username used to authenticate at server_url wiki (unicode)
    @param password: password of <username> (unicode)
    @param groupname: group page name (unicode)
    @param groupdesc: group description (unicode)
    @param groupmembers: group member names (list of unicode)
    @param acl: Access Control List value (optional, unicode)
    """
    wiki = xmlrpclib.ServerProxy(server_url)
    auth_token = wiki.getAuthToken(username, password)
    assert auth_token, 'Invalid username/password'

    # Verify that the token is valid by using it
    # and checking that the result is 'SUCCESS'.
    # The token should be valid for 15 minutes.
    assert wiki.applyAuthToken(auth_token) == 'SUCCESS'

    try:
        # build a multicall object that
        mcall = xmlrpclib.MultiCall(wiki)
        # first applies the token and
        mcall.applyAuthToken(auth_token)
        # then creates/updates the group page
        mcall.UpdateGroup(groupname, groupdesc, groupmembers, acl)
        # now execute the multicall
        results = mcall()

        # everything should have worked
        # instead of the asserts you can have anything else
        # but you should definitely access all the results
        # once so that faults are checked and raised
        assert results[0] == 'SUCCESS'
        # TODO: process other results / xmlrpc faults
    finally:
        # be nice to the server and clean up the token
        # regardless of what happened
        assert wiki.deleteAuthToken(auth_token) == 'SUCCESS'


if __name__ == "__main__":
    # xmlrpc url of target wiki, where the group pages shall get created
    server_url = "http://master.moinmo.in/?action=xmlrpc2"
    # user and password of a wiki user of the target wiki with enough priviledges
    username = "ThomasWaldmann"
    password = "wrong"

    # data for the group page:
    groupname = u"TestGroup"
    groupdesc = u"Just a test group"
    groupmembers = [u'JoeDoe', u'JaneDoe', ]
    acl = "All:read,write,delete" # optional, can be empty

    updateGroup(server_url, username, password, groupname, groupdesc, groupmembers, acl)

