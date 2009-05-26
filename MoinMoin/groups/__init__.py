# -*- coding: iso-8859-1 -*-

"""
MoinMoin - group definition access via various backends.

TODO Group name mapping for the BackendManager.

@copyright: 2009 DmitrijsMilajevs
@license: GPL, see COPYING for details
"""


class BackendManager(object):
    """
    BackendManager maps string to the Group object. String represents
    group name. It provides access to groups of specific backend.
    """

    def __init__(self, backend):
        """
        Creates backend manager object.

        @type backend: group backend object.
        @param backend: the backend which provides access to the group
        definitions.
        """
        self._backend = backend

    def __getitem__(self, group_name):
        """
        Selection of a group by its name.

        @type group_name: unicode string.
        @param group_name: name of the group which object to select.
        """
        return self._backend[group_name]

    def __iter__(self):
        """
        Iteration over group names.
        """
        return iter(self._backend)

    def __contains__(self, group_name):
        """
        Check if a group called group name is avaliable via this backend.

        @type group_name: unicode string.
        @param group_name: name of the group which is checked for an containment.
        """
        return group_name in self._backend

    def membergroups(self, member):
        """
        List all groups where member is a member of.
        @rtype: list of unicode strings
        @return: list of group names in which member takes part in
        """
        return [group_name for group_name in self
                         if member in self[group_name]]


class GroupManager(object):
    """
    GroupManager manages several group backends.
    """

    def __init__(self, backends):
        """
        Create a group manager object.

        @type backends: list of objects.
        @param backend: group backends which are used to get access to the
        group definitions.
        """
        self._backends = backends

    def __getitem__(self, group_name):
        """
        Selection of a group by its name.
        """
        for backend in self._backends:
            if group_name in backend:
                return backend[group_name]
        raise KeyError("There is no such group")

    def __iter__(self):
        """
        Iteration over groups names.
        """
        yielded_groups = set()

        for backend in self._backends:
            for group_name in backend:
                if group_name not in yielded_groups:
                    yield group_name
                    yielded_groups.add(group_name)

    def __contains__(self, group_name):
        """
        Check if a group called group_name is defined.
        """
        for backend in self._backends:
            if group_name in backend:
                return True

    def membergroups(self, member):
        """
        List all groups where member is a member of.
        @rtype: list of unicode strings
        @return: list of group names in which member takes part in
        """
        return [group_name for group_name in self
                         if member in self[group_name]]
