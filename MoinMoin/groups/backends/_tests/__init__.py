# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.groups.backends base test classes.

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2008 by MoinMoin:MelitaMihaljevic
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.

"""

from py.test import raises

from MoinMoin import security
from MoinMoin._tests import wikiconfig

class Config(wikiconfig.Config):
    # Simply drop the "Group" postfix for group names given to a backend.
    # Note: in the real world, this would not work good enough:
    to_backend_name = lambda self, group_name:  group_name[:-5]
    # Add "Group" postfix for group names received from a backend.
    # Note: in the real world, this would not work good enough:
    to_group_name = lambda self, backend_name:'%sGroup' % backend_name

class BackendTest(object):

    test_groups = {u'EditorGroup': [u'AdminGroup', u'John', u'JoeDoe', u'Editor1'],
                   u'AdminGroup': [u'Admin1', u'Admin2', u'John'],
                   u'OtherGroup': [u'SomethingOther'],
                   u'RecursiveGroup': [u'Something', u'OtherRecursiveGroup'],
                   u'OtherRecursiveGroup': [u'RecursiveGroup', u'Anything'],
                   u'ThirdRecursiveGroup': [u'ThirdRecursiveGroup', u'Banana']}

    expanded_groups = {u'EditorGroup': [u'Admin1', u'Admin2', u'John',
                                        u'JoeDoe', u'Editor1'],
                       u'AdminGroup': [u'Admin1', u'Admin2', u'John'],
                       u'OtherGroup': [u'SomethingOther'],
                       u'RecursiveGroup': [u'Anything', u'Something'],
                       u'OtherRecursiveGroup': [u'Anything', u'Something'],
                       u'ThirdRecursiveGroup': [u'Banana']}

    # These backend group names do not follow moin convention:
    mapped_groups = {u'Editor': [u'Admin', u'John', u'JoeDoe', u'Editor1'],
                     u'Admin': [u'Admin1', u'Admin2', u'John'],
                     u'Other': [u'SomethingOther'],
                     u'Recursive': [u'Something', u'OtherRecursive'],
                     u'OtherRecursive': [u'Recursive', u'Anything'],
                     u'ThirdRecursive': [u'ThirdRecursive', u'Banana']}

    def test_contains(self):
        """
        Test group_wiki Backend and Group containment methods.
        """
        groups = self.request.groups

        for (group, members) in self.expanded_groups.iteritems():
            print group
            assert group in groups
            for member in members:
                assert member in groups[group]

        raises(KeyError, lambda: groups[u'NotExistingGroup'])

    def test_iter(self):
        groups = self.request.groups

        for (group, members) in self.expanded_groups.iteritems():
            returned_members = [x for x in groups[group]]
            assert len(returned_members) == len(members)
            for member in members:
                assert member in returned_members

    def test_membergroups(self):
        groups = self.request.groups

        john_groups = groups.membergroups(u'John')
        assert 2 == len(john_groups)
        assert u'EditorGroup' in john_groups
        assert u'AdminGroup' in john_groups
        assert u'ThirdGroup' not in john_groups

    def test_backend_acl_allow(self):
        """
        Test if the wiki group backend works with acl code.
        Check user which has rights.
        """
        request = self.request

        acl_rights = ["AdminGroup:admin,read,write"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        allow = acl.may(request, u"Admin1", "admin")

        assert allow, 'Admin has read rights because he is member of AdminGroup'

    def test_backend_acl_deny(self):
        """
        Test if the wiki group backend works with acl code.
        Check user which does not have rights.
        """
        request = self.request

        acl_rights = ["AdminGroup:read,write"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        other_user_allow = acl.may(request, u"OtherUser", "admin")
        some_user_allow = acl.may(request, u"SomeUser", "read")

        assert not other_user_allow, 'OtherUser does not have admin rights because it is not listed in acl'
        assert not some_user_allow, 'SomeUser does not have admin read right because he is not listed in the AdminGroup'

    def test_wiki_backend_page_acl_with_all(self):
        request = self.request

        acl_rights = ["EditorGroup:read,write,delete,admin All:read"]
        acl = security.AccessControlList(request.cfg, acl_rights)


        for member in self.expanded_groups[u'EditorGroup']:
            assert acl.may(request, member, "read")
            assert acl.may(request, member, "write")
            assert acl.may(request, member, "delete")
            assert acl.may(request, member, "admin")

        assert acl.may(request, u"Someone", "read")
        assert not acl.may(request, u"Someone", "write")
        assert not acl.may(request, u"Someone", "delete")
        assert not acl.may(request, u"Someone", "admin")

class BackendTestMapping(BackendTest):
    """
    Test group name mapping:
        moin -> backend (e.g. "AdminGroup" -> "ImportantAdminGroup")
        backend -> moin (e.g. "ImportantAdminGroup" -> "AdminGroup")

    Moin expects group names to match the page_group_regex (e.g. "AdminGroup"),
    but a backend might want to use different group names (e.g. just "ImportantAdminGroup").
    """
    test_groups = {u'ImportantEditorGroup': [u'ImportantAdminGroup', u'John',
                                             u'JoeDoe', u'Editor'],
                   u'ImportantAdminGroup': [u'Admin', u'Admin2', u'John'],
                   u'ImportantOtherGroup': [u'SomethingOther'],
                   u'ImportantRecursiveGroup': [u'Something', u'ImportantOtherRecursiveGroup'],
                   u'ImportantOtherRecursiveGroup': [u'ImportantRecursiveGroup', u'Anything'],
                   u'ImportantThirdRecursiveGroup': [u'ImportantThirdRecursiveGroup', u'Banana']}


coverage_modules = ['MoinMoin.groups.backends.config_group']

