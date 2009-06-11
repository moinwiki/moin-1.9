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

    def __init__(self, backends):
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
        """
        List all group names of the groups where <member> is a member of.

        @param member: member name [unicode]
        @return: list of group names [unicode]
        """
        return [group_name for group_name in self
                if member in self[group_name]]

    def update_cache(self):
        for backend in self._backends:
            update_cache = getattr(backend, 'update_cache', None)
            if callable(update_cache):
                update_cache()

    def load_cache(self):
        for backend in self._backends:
            load_cache = getattr(backend, 'load_cache', None)
            if callable(load_cache):
                load_cache()

    def __repr__(self):
        return "<%s backends=%s>" % (self.__class__, self._backends)

