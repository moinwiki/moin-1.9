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
        backend_group_name = self.to_backend_name(self.name)

        members_final = set()
        member_groups = set()

        for member in self._backend._groups[backend_group_name]:
            if member in self._backend._groups:
                member_groups.add(self.to_group_name(member))
            else:
                members_final.add(member)

        self.members = members_final
        self.member_groups = member_groups


class Backend(BaseBackend):

    def __init__(self, request, groups=None):
        """
        @param groups: Dictionary of groups where key is group name,
        and value is list of members of that group.

        If <groups> is not defined request.cfg.config_groups is used.
        """
        super(Backend, self).__init__(request)

        if groups is not None:
            self._groups = groups
        else:
            self._groups = request.cfg.config_groups

    def __contains__(self, group_name):
        backend_group_name = self.to_backend_name(group_name)
        return self.page_group_regex.match(group_name) and backend_group_name in self._groups

    def __iter__(self):
        backend_group_names = self._groups.keys()
        return (self.to_group_name(backend_group_name) for backend_group_name in backend_group_names)

    def __getitem__(self, group_name):
        return Group(request=self.request, name=group_name, backend=self)
