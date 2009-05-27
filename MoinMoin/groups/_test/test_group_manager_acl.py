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
        pass

    def setup_class(self):
        groups = {u'FirstGroup': frozenset([u"ExampleUser", u"SecondUser", u"JoeDoe"]),
                  u'SecondGroup': frozenset([u"ExampleUser", u"ThirdUser"])}
        group_manager = GroupManager([BackendManager(groups)])

        self.Config.group_manager = group_manager

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

    def testConfigBackend(self):
        """
        tests getting a group from the group manager, does group
        membership tests.
        """
        # define config groups
        groups = {'A': set(['a1', 'a2']),
                  'B': set(['b1', 'b2']),
                 }

        # create config group manager backend object
        group_manager_backend = GroupManager(BackendManager([groups]))

        # check that a group named 'A' is available via the config backend
        assert 'A' in group_manager_backend

        # check that a group named 'C' is not available via the config backend
        assert 'C' not in group_manager_backend

        # get group object for a group named 'A'
        group_A = group_manager_backend['A']

        # check that a1 is a member of group A
        assert 'a1' in group_A

        # check that b1 is not a member of group A
        assert 'b1' not in group_A

coverage_modules = ['MoinMoin.groups']
