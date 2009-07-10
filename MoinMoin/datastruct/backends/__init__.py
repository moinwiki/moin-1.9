# -*- coding: iso-8859-1 -*-
"""
MoinMoin - base classes for datastruct backends.

@copyright: 2009 MoinMoin:DmitrijsMilajevs
@license: GPL, see COPYING for details
"""


class GroupDoesNotExistError(Exception):
    """
    Raised when a group name is not found in the backend.
    """


class DictDoesNotExistError(Exception):
    """
    Raised when a dict name is not found in the backend.
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

    def __contains__(self, member, processed_groups=None):
        """
        First check if <member> is part of this group and then check
        for every subgroup in this group.

        <processed_groups> is needed to avoid infinite recursion, if
        groups are defined recursively.

        @param member: member name [unicode]
        @param processed_groups: groups which were checked for containment before [set]
        """

        if not processed_groups:
            processed_groups = set()

        processed_groups.add(self.name)

        if member in self.members or member in self.member_groups:
            return True
        else:
            groups = self.request.groups
            for group_name in self.member_groups:
                if group_name not in processed_groups and group_name in groups and groups[group_name].__contains__(member, processed_groups):
                    return True

        return False

    def __iter__(self, yielded_members=None, processed_groups=None):
        """
        Iterate first over members of this group, then over subgroups of this group.

        <yielded_members> and <processed_groups> are needed to avoid infinite recursion.
        This can happen if there are two groups like these:
           OneGroup: Something, OtherGroup
           OtherGroup: OneGroup, SomethingOther

        @param yielded_members: members which have been already yielded before [set]
        @param processed_groups: group names which have been iterated before [set]
        """

        if not processed_groups:
            processed_groups = set()

        if not yielded_members:
            yielded_members = set()

        processed_groups.add(self.name)

        for member in self.members:
            if member not in yielded_members:
                yielded_members.add(member)
                yield member

        groups = self.request.groups
        for group_name in self.member_groups:
            if group_name not in processed_groups:
                if group_name in groups:
                    for member in groups[group_name].__iter__(yielded_members, processed_groups):
                        yield member
                else:
                    yield group_name

    def __repr__(self):
        return "<%s name=%s members=%s member_groups=%s>" % (self.__class__,
                                                             self.name,
                                                             self.members,
                                                             self.member_groups)


class BaseGroupsBackend(object):

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


class BaseDict(object):

    def __init__(self, request, name, backend):
        """
        Initialize a dict.

        @param request
        @param name: moin dict name
        @backend: backend object which created this object
        """
        self.request = request
        self.name = name
        self._backend = backend
        self._dict = self._load_dict()

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()

    def __getitem__(self, key):
        return self._dict[key]

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def _load_dict(self):
        """
        Retrieve dict data from the backend.
        """
        return self._backend._retrieve_items(self.name)

    def __repr__(self):
        return "<%r name=%r items=%r>" % (self.__class__, self.name, self._dict.items())


class BaseDictsBackend(object):

    def __init__(self, request):
        self.request = request
        self.page_dict_regex = request.cfg.cache.page_dict_regexact

    def is_dict_name(self, name):
        return self.page_dict_regex.match(name)

    def __contains__(self, dict_name):
        """
        Check if a dict called <dict_name> is available in this backend.
        """
        raise NotImplementedError()

    def __getitem__(self, dict_name):
        """
        Get a dict by its moin dict name.
        """
        raise NotImplementedError()

    def _retrieve_items(self, dict_name):
        raise NotImplementedError()

