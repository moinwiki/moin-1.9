# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.datastruct.backends base test classes.

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2008 by MoinMoin:MelitaMihaljevic
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.

"""

from py.test import raises

from MoinMoin import security
from MoinMoin.datastruct import GroupDoesNotExistError


class GroupsBackendTest(object):

    test_groups = {u'EditorGroup': [u'AdminGroup', u'John', u'JoeDoe', u'Editor1', u'John'],
                   u'AdminGroup': [u'Admin1', u'Admin2', u'John'],
                   u'OtherGroup': [u'SomethingOther'],
                   u'RecursiveGroup': [u'Something', u'OtherRecursiveGroup'],
                   u'OtherRecursiveGroup': [u'RecursiveGroup', u'Anything'],
                   u'ThirdRecursiveGroup': [u'ThirdRecursiveGroup', u'Banana'],
                   u'EmptyGroup': []}


    expanded_groups = {u'EditorGroup': [u'Admin1', u'Admin2', u'John',
                                        u'JoeDoe', u'Editor1'],
                       u'AdminGroup': [u'Admin1', u'Admin2', u'John'],
                       u'OtherGroup': [u'SomethingOther'],
                       u'RecursiveGroup': [u'Anything', u'Something'],
                       u'OtherRecursiveGroup': [u'Anything', u'Something'],
                       u'ThirdRecursiveGroup': [u'Banana'],
                       u'EmptyGroup': []}

    def test_contains(self):
        """
        Test group_wiki Backend and Group containment methods.
        """
        groups = self.request.groups

        for group, members in self.expanded_groups.iteritems():
            assert group in groups
            for member in members:
                assert member in groups[group]

        raises(GroupDoesNotExistError, lambda: groups[u'NotExistingGroup'])

    def test_contains_group(self):
        groups = self.request.groups

        assert u'AdminGroup' in groups[u'EditorGroup']
        assert u'EditorGroup' not in groups[u'AdminGroup']

    def test_iter(self):
        groups = self.request.groups

        for group, members in self.expanded_groups.iteritems():
            returned_members = list(groups[group])
            assert len(returned_members) == len(members)
            for member in members:
                assert member in returned_members

    def test_get(self):
        groups = self.request.groups

        assert groups.get(u'AdminGroup')
        assert u'NotExistingGroup' not in groups
        assert groups.get(u'NotExistingGroup') is None

    def test_groups_with_member(self):
        groups = self.request.groups

        john_groups = list(groups.groups_with_member(u'John'))
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

    def test_backend_acl_with_all(self):
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

    def test_backend_acl_not_existing_group(self):
        request = self.request
        assert u'NotExistingGroup' not in request.groups

        acl_rights = ["NotExistingGroup:read,write,delete,admin All:read"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        assert not acl.may(request, u"Someone", "write")


class DictsBackendTest(object):

    dicts = {u'SomeTestDict': {u'First': u'first item',
                               u'text with spaces': u'second item',
                               u'Empty string': u'',
                               u'Last': u'last item'},
             u'SomeOtherTestDict': {u'One': '1',
                                    u'Two': '2'}}

    def test_getitem(self):
        expected_dicts = self.dicts
        dicts = self.request.dicts

        for dict_name, expected_dict in expected_dicts.items():
            test_dict = dicts[dict_name]
            assert len(test_dict) == len(expected_dict)
            for key, value in expected_dict.items():
                assert test_dict[key] == value

    def test_contains(self):
        dicts = self.request.dicts

        for key in self.dicts:
            assert key in dicts

        assert u'SomeNotExistingDict' not in dicts

