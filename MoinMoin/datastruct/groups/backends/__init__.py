# -*- coding: iso-8859-1 -*-
"""
MoinMoin - base classes for group backends.

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""


class GroupDoesNotExistError(Exception):
    """
    Raised when a group name is not found in the backend.
    """


class BaseGroup(object):

    def __init__(self, request, name, backend):
        """
        Initialize a group.

        @param request
        @param name: moin group name
        @backend: backend object which created this object

        """
        self.request = request
        self.name = name
        self._backend = backend
        self.members, self.member_groups = self._load_group()

    def _load_group(self):
        """
        Retrieve group data from the backend and filter it to members and group_members.
        """
        members_retrieved = set(self._backend._retrieve_members(self.name))

        member_groups = set(member for member in members_retrieved if self._backend.is_group(member))
        members = members_retrieved - member_groups

        return members, member_groups

    def _contains(self, member, processed_groups):
        """
        First check if <member> is part of this group and then check
        for every subgroup in this group.

        <processed_groups> is needed to avoid infinite recursion, if
        groups are defined recursively.

        @param member: member name [unicode]
        @param processed_groups: groups which were checked for containment before [set]
        """
        processed_groups.add(self.name)

        if member in self.members or member in self.member_groups:
            return True
        else:
            groups = self.request.groups
            for group_name in self.member_groups:
                if group_name not in processed_groups and groups[group_name]._contains(member, processed_groups):
                    return True

        return False

    def __contains__(self, member):
        """
        Check if <member> is defined in this group. Checks also for subgroups.
        """
        return self._contains(member, set())

    def _iter(self, yielded_members, processed_groups):
        """
        Iterate first over members of this group, then over subgroups of this group.

        <yielded_members> and <processed_groups> are needed to avoid infinite recursion.
        This can happen if there are two groups like these:
           OneGroup: Something, OtherGroup
           OtherGroup: OneGroup, SomethingOther

        @param yielded_members: members which have been already yielded before [set]
        @param processed_groups: group names which have been iterated before [set]
        """
        processed_groups.add(self.name)

        for member in self.members:
            if member not in yielded_members:
                yielded_members.add(member)
                yield member

        groups = self.request.groups
        for group_name in self.member_groups:
            if group_name not in processed_groups:
                for member in groups[group_name]._iter(yielded_members, processed_groups):
                    yield member

    def __iter__(self):
        """
        Iterate over members of this group. Iterates also over subgroups if any.
        """
        return self._iter(set(), set())

    def __repr__(self):
        return "<%s name=%s members=%s member_groups=%s>" % (self.__class__,
                                                             self.name,
                                                             self.members,
                                                             self.member_groups)


class BaseBackend(object):

    def __init__(self, request):
        self.request = request
        self.page_group_regex = request.cfg.cache.page_group_regexact

    def is_group(self, member):
        return self.page_group_regex.match(member)

    def __contains__(self, group_name):
        """
        Check if a group called <group_name> is available in this backend.
        """
        raise NotImplementedError()

    def __iter__(self):
        """
        Iterate over moin group names of the groups defined in this backend.

        @return: moin group names
        """
        raise NotImplementedError()

    def __getitem__(self, group_name):
        """
        Get a group by its moin group name.
        """
        raise NotImplementedError()

    def __repr__(self):
        return "<%s groups=%s>" % (self.__class__, list(self))

    def _retrieve_members(self, group_name):
        raise NotImplementedError()

    def groups_with_member(self, member):
        """
        List all group names of groups containing <member>.

        @param member: member name [unicode]
        @return: list of group names [unicode]
        """
        for group_name in self:
            try:
                if member in self[group_name]:
                    yield group_name
            except GroupDoesNotExistError:
                pass

    def get(self, key, default=None):
        if key in self:
            return self[key]
        else:
            return default

