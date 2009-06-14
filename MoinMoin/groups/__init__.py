# -*- coding: iso-8859-1 -*-
"""
MoinMoin - group access via various backends.

@copyright: 2009 DmitrijsMilajevs
@license: GPL, see COPYING for details
"""


class GroupManager(object):
    """
    GroupManager manages several group backends.
    """

    def __init__(self, *backends):
        """
        Create a group manager object.

        @param backends: list of group backends which are used to get
                         access to the group definitions.
        """
        self._backends = backends

    def __getitem__(self, group_name):
        """
        Get a group by its name. First match counts.

        @param group_name: name of the group [unicode]
        """
        for backend in self._backends:
            if group_name in backend:
                return backend[group_name]
        raise KeyError("There is no such group %s" % group_name)

    def __iter__(self):
        """
        Iterate over group names in all backends (filtering duplicates).
        """
        yielded_groups = set()

        for backend in self._backends:
            for group_name in backend:
                if group_name not in yielded_groups:
                    yield group_name
                    yielded_groups.add(group_name)

    def __contains__(self, group_name):
        """
        Check if a group called group_name is available in any of the backends.

        @param group_name: name of the group [unicode]
        """
        for backend in self._backends:
            if group_name in backend:
                return True
        return False

    def membergroups(self, member):
        # Dirty hack just to make code works, after GroupManager
        # becomes a backend itself, no need in this.
        return self._backends[0].groups_with_member(member)

    def __repr__(self):
        return "<%s backends=%s>" % (self.__class__, self._backends)

