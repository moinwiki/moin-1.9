# -*- coding: iso-8859-1 -*-

"""
MoinMoin.groups.GroupManager test

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

from py.test import raises

from MoinMoin.groups import BackendManager, GroupManager


class TestGroupManager(object):

    def setup_method(self, method):

        self.admin_group = frozenset([u'Admin', u'JohnDoe'])
        self.editor_group = frozenset([u'MainEditor', u'JohnDoe'])
        self.fruit_group = frozenset([u'Apple', u'Banana', u'Cherry'])

        first_backend = BackendManager({u'AdminGroup': self.admin_group,
                                        u'EditorGroup': self.editor_group,
                                        u'FruitGroup': self.fruit_group})

        self.user_group = frozenset([u'JohnDoe', u'Bob', u'Joe'])
        self.city_group = frozenset([u'Bolzano', u'Riga', u'London'])
        # Suppose, someone hacked second backend
        # and added himself to AdminGroup
        self.second_admin_group = frozenset([u'TheHacker'])

        second_backend = BackendManager({u'UserGroup': self.user_group,
                                         u'CityGroup': self.city_group,
                                         # Here group name clash accours.
                                         # AdminGroup is defined in both
                                         # first_backend and second_backend.
                                         u'AdminGroup': self.second_admin_group})

        self.group_manager = GroupManager(backends = [first_backend,
                                                      second_backend])

    def test_getitem(self):
        assert self.fruit_group == self.group_manager[u'FruitGroup']
        raises(KeyError, lambda: self.group_manager[u'not existing group'])

    def test_clashed_getitem(self):
        admin_group = self.group_manager[u'AdminGroup']

        assert self.admin_group == admin_group

        # Nevertheless, TheHacker added himself to the second backend,
        # it must not be taken into consideration, because AdminGroup is defined
        # in first backend
        assert u'TheHacker' not in admin_group

    def test_itar(self):
        all_group_names = [group_name for group_name in self.group_manager]

        assert 5 == len(all_group_names)
        # There are no dublicates
        assert len(set(all_group_names)) == len(all_group_names)

    def test_contains(self):
        assert u'UserGroup' in self.group_manager
        assert u'not existing group' not in self.group_manager

    def test_membergroups(self):
        apple_groups = self.group_manager.membergroups(u'Apple')
        assert 1 == len(apple_groups)
        assert u'FruitGroup' in apple_groups
        assert u'AdminGroup' not in apple_groups

        john_doe_groups = self.group_manager.membergroups(u'JohnDoe')
        assert 3 == len(john_doe_groups)
        assert u'EditorGroup' in john_doe_groups
        assert u'AdminGroup' in john_doe_groups
        assert u'UserGroup' in john_doe_groups
        assert u'FruitGroup' not in john_doe_groups

coverage_modules = ['MoinMoin.groups']
