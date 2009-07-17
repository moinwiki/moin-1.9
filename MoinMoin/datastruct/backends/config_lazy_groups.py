# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - config group lazy backend.

    The config group backend allows defining groups in a configuration
    file. These backends do not store members internally, but get them
    from backend when needed in a lazy way.

    NOTE, the backends are experimental and are implemented to find
    out how different backends, for example, LDAP backend, should
    work.

    @copyright: 2009 MoinMoin:DmitrijsMilajevs
    @license: GPL, see COPYING for details
"""

import time

from MoinMoin.datastruct.backends import BaseGroup, BaseGroupsBackend, GroupDoesNotExistError


class Proxy(object):
    """
    This class is done just to emulate that group definition is
    something external.

    For the LDAP backend this class not needed. __contains__ and
    __iter__ may be defined in a Group class.
    """

    def __init__(self, groups):
        """
        Although, groups are passed, it doesn't look like
        something lazy, it the best solution i can find now.
        """
        self._groups = groups

    def __contains__(self, group_name):
        return group_name in self._groups

    def __iter__(self):
        return self._groups.iterkeys()

    def iter_group(self, group_name):
        if group_name in self:
            for member in self._groups[group_name]:
                # Imitate slow connection
                time.sleep(0.1)
                yield member

    def has_member(self, group_name, member):
        # Imitate slow connection
        time.sleep(0.1)
        return group_name in self and member in self._groups[group_name]


class LazyGroup(BaseGroup):

    def __init__(self, request, name, backend):
        super(LazyGroup, self).__init__(request, name, backend)

        if name not in backend:
            raise GroupDoesNotExistError(name)

        self.proxy = backend._proxy

    def __contains__(self, member, processed_groups=None):
        return self.proxy.has_member(self.name, member)

    def __iter__(self, yielded_members=None, processed_groups=None):
        if not yielded_members:
            yielded_members = set()

        for member in self.proxy.iter_group(self.name):
            if member not in yielded_members:
                yielded_members.add(member)
                yield member


class LazyConfigGroups(BaseGroupsBackend):

    def __init__(self, request, groups):
        """
        @param groups: Dictionary of groups where key is a group name,
        and value is a list of members of that group.
        """
        super(LazyConfigGroups, self).__init__(request)

        self._proxy = Proxy(groups)

    def __contains__(self, group_name):
        return group_name in self._proxy

    def __iter__(self):
        return self._proxy.__iter__()

    def __getitem__(self, group_name):
        return LazyGroup(request=self.request, name=group_name, backend=self)

