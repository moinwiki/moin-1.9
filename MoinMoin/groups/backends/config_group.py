# -*- coding: iso-8859-1 -*-
"""
MoinMoin - config group backend

The config group backend enables you to define groups in a configuration file.

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

from MoinMoin.groups.backends import BaseGroup, BaseBackend


class Group(BaseGroup):

    def _load_group(self):
        request = self.request

        members_final = set()
        member_groups = set()

        for member in self._backend._groups[self.name]:
            if member in self._backend._groups:
                member_groups.add(member)
            else:
                members_final.add(member)

        self.members = members_final
        self.member_groups = member_groups


class Backend(BaseBackend):

    def __init__(self, request, groups):
        """
        @param groups: Dictionary of groups where key is group name,
        and value is list of members of that group.
        """
        super(Backend, self).__init__(request)

        self._groups = groups

    def __contains__(self, group_name):
        return self.page_group_regex.match(group_name) and group_name in self._groups

    def __iter__(self):
        return iter(self._groups.keys())

    def __getitem__(self, group_name):
        return Group(request=self.request, name=group_name, backend=self)
