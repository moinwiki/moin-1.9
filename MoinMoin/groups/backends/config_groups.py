# -*- coding: iso-8859-1 -*-
"""
MoinMoin - config group backend

The config group backend enables you to define groups in a configuration file.

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

from MoinMoin.groups.backends import BaseGroup, BaseBackend, GroupDoesNotExistError


class Group(BaseGroup):
    pass


class ConfigGroups(BaseBackend):

    def __init__(self, request, groups):
        """
        @param groups: Dictionary of groups where key is group name,
        and value is list of members of that group.
        """
        super(ConfigGroups, self).__init__(request)

        self._groups = groups

    def __contains__(self, group_name):
        return self.page_group_regex.match(group_name) and group_name in self._groups

    def __iter__(self):
        return self._groups.iterkeys()

    def __getitem__(self, group_name):
        return Group(request=self.request, name=group_name, backend=self)

    def _retrieve_members(self, group_name):
        try:
            return self._groups[group_name]
        except KeyError:
            raise GroupDoesNotExistError(group_name)

