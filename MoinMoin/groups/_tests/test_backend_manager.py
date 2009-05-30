# -*- coding: iso-8859-1 -*-

"""
MoinMoin.groups.BackendManager test

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

from py.test import raises

from MoinMoin.groups import BackendManager


class TestBackendManagerAPI(object):
    """
    This tastcase test Backend manager API
    """

    def setup_method(self, method):
        self.admin_group = frozenset([u'Admin', u'JohnDoe'])
        self.editor_group = frozenset([u'MainEditor', u'JohnDoe'])
        self.fruit_group = frozenset([u'Apple', u'Banana'])

        groups = {u'AdminGroup': self.admin_group,
                  u'EditorGroup': self.editor_group,
                  u'FruitGroup': self.fruit_group}

        self.group_backend = BackendManager(backend=groups)

    def test_getitem(self):
        """
        Test of the __getitem__ API method. It should return a group
        object by the group name.
        """
        assert self.admin_group == self.group_backend[u'AdminGroup']
        assert self.fruit_group == self.group_backend[u'FruitGroup']

        raises(KeyError, lambda: self.group_backend[u'not existing group'])

    def test_contains(self):
        """
        Test of the __contains__ API method. It checks if a group is
        avaliable via this backend. Check is done by group's name.
        """
        assert u'AdminGroup' in self.group_backend
        assert u'FruitGroup' in self.group_backend

        assert u'not existing group' not in self.group_backend

    def  test_membergroups(self):
        """
        Test of membergroups API method. It lists all groups where
        member is a member of. It should  return a list of group names.
        """
        apple_groups = self.group_backend.membergroups(u'Apple')
        assert 1 == len(apple_groups)
        assert u'FruitGroup' in apple_groups
        assert u'AdminGroup' not in apple_groups

        john_doe_groups = self.group_backend.membergroups(u'JohnDoe')
        assert 2 == len(john_doe_groups)
        assert u'EditorGroup' in john_doe_groups
        assert u'AdminGroup' in john_doe_groups
        assert u'FruitGroup' not in john_doe_groups


class TestManagerMapping(object):
    """
    This class tests mapping of the group names from a backend to the
    moin and from the moin to a backend.

    Here the simplest situation is considered. Moin expect groups to
    be named as *Group, but backend stores group names without this prefix.

    When group names are passed or retrieved from the backend they
    should be mapped.
    """

    def setup_class(self):
        self.admin_group = frozenset([u'Admin', u'JohnDoe'])
        self.editor_group = frozenset([u'MainEditor', u'JohnDoe'])

        # Group names here do not follow moin convention: they do not
        # have group prefix.
        groups = {u'Admin': self.admin_group,
                  u'Editor': self.editor_group}

        # Simply drop last five letters, what is length of word "Group"
        mapper_to_backend = lambda group_name: group_name[:-5]
        # Add "Group" postfix for every group name received from a backend
        mapper_from_backend = lambda group_name: "%sGroup" % group_name

        self.group_backend = BackendManager(backend=groups,
                                            mapper_to_backend=mapper_to_backend,
                                            mapper_from_backend=mapper_from_backend)


    def test_getitem(self):
        admin_group = self.group_backend[u'AdminGroup']
        assert self.admin_group == admin_group

    def test_contains(self):
        assert u'AdminGroup' in self.group_backend

    def test_membersgroups(self):
        assert u'AdminGroup' in self.group_backend.membergroups(u'JohnDoe')

coverage_modules = ['MoinMoin.groups']
