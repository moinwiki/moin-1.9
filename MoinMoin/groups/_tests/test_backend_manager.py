# -*- coding: iso-8859-1 -*-

"""
MoinMoin.groups.BackendManager test

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

from py.test import raises

from MoinMoin.groups import BackendManager


class TestBackendManager(object):

    def setup_method(self, method):
        self.admin_group = frozenset([u'Admin', u'JohnDoe'])
        self.editor_group = frozenset([u'MainEditor', u'JohnDoe'])
        self.fruit_group = frozenset([u'Apple', u'Banana'])

        groups = {u'AdminGroup': self.admin_group,
                  u'EditorGroup': self.editor_group,
                  u'FruitGroup': self.fruit_group}

        self.group_backend = BackendManager(backend=groups)

    def test_getitem(self):
        assert self.admin_group == self.group_backend[u'AdminGroup']
        assert self.fruit_group == self.group_backend[u'FruitGroup']

        raises(KeyError, lambda: self.group_backend[u'not existing group'])

    def test_contains(self):
        assert u'AdminGroup' in self.group_backend
        assert u'FruitGroup' in self.group_backend

        assert u'not existing group' not in self.group_backend

    def  test_membergroups(self):
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
    Test group name mapping:
        moin -> backend (e.g. "AdminGroup" -> "Admin")
        backend -> moin (e.g. "Admin" -> "AdminGroup")

    Moin expects group names to match the page_group_regex (e.g. "AdminGroup"),
    but a backend might want to use different group names (e.g. just "Admin").
    """

    def setup_class(self):
        self.admin_group = frozenset([u'Admin', u'JohnDoe'])
        self.editor_group = frozenset([u'MainEditor', u'JohnDoe'])

        # These backend group names do not follow moin convention:
        groups = {u'Admin': self.admin_group,
                  u'Editor': self.editor_group}

        # Simply drop the "Group" postfix for group names given to a backend.
        # Note: in the real world, this would not work good enough:
        mapper_to_backend = lambda group_name: group_name[:-5]

        # Add "Group" postfix for group names received from a backend.
        # Note: in the real world, this would not work good enough:
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
