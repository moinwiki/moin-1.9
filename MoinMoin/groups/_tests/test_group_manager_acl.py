# -*- coding: iso-8859-1 -*-
"""
MoinMoin.groups.GroupManager ACL Tests

@copyright: 2009 MoinMoin:DmitrijsMilajevs
            2008 MoinMoin:MelitaMihaljevic
@license: GPL, see COPYING for details
"""

from MoinMoin import security
from MoinMoin.groups import BackendManager, GroupManager


class TestGroupManagerACL:
    """
    Test how GroupManager works with acl code.
    """

    from MoinMoin._tests import wikiconfig
    class Config(wikiconfig.Config):
        def group_manager_init(self, request):
            groups = {u'FirstGroup': frozenset([u"ExampleUser", u"SecondUser", u"JoeDoe"]),
                      u'SecondGroup': frozenset([u"ExampleUser", u"ThirdUser"])}

            return GroupManager(backends=[BackendManager(backend=groups)])

    def testConfigBackendAcl(self):
        """
        test if the group config backend works with acl code
        """
        # define acl rights for FirstGroup, members of group can read and write
        acl_rights = ["FirstGroup:admin,read,write"]
        acl = security.AccessControlList(self.request.cfg, acl_rights)

        allow = acl.may(self.request, u"JoeDoe", "admin")
        # JoeDoe has admin rights because he is a member of group FirstGroup
        assert allow

        allow = acl.may(self.request, u"AnotherUser", "admin")
        # AnotherUser has no read rights because he is not a member of group FirstGroup
        assert not allow


coverage_modules = ['MoinMoin.groups']
