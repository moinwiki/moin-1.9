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


class BackendTest(object):

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

        raises(KeyError, lambda: groups[u'NotExistingGroup'])

    def test_iter(self):
        groups = self.request.groups

        for group, members in self.expanded_groups.iteritems():
            returned_members = list(groups[group])
            assert len(returned_members) == len(members)
            for member in members:
                assert member in returned_members

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


coverage_modules = ['MoinMoin.groups.backends.config_group']

