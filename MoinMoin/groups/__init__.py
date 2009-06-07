# -*- coding: iso-8859-1 -*-
"""
MoinMoin - group access via various backends.

@copyright: 2009 DmitrijsMilajevs
@license: GPL, see COPYING for details
"""


class BackendManager(object):
    """
    A BackendManager maps a group name to a Group object.
    It provides access to groups of one specific backend.
    """

    def __init__(self, backend, mapper_to_backend=lambda x: x, mapper_from_backend=lambda x: x):
        """
        Create backend manager object.

        XXX Decorators can be used for group name mapping.

        @param request: request object.

        @param backend: the group backend which provides access to the
                        group definitions.

        @param mapper_to_backend: a function mapping the moin group
                                  name to the backend group name

        @param mapper_from_backend: a function mapping the backend
                                    group name to the moin group name
        """
        self._backend = backend
        self.mapper_to_backend = mapper_to_backend
        self.mapper_from_backend =  mapper_from_backend

    def __getitem__(self, group_name):
        """
        Get a group by its name.

        @param group_name: name of the group [unicode]
        """
        return self._backend[self.mapper_to_backend(group_name)]

    def __iter__(self):
        """
        Iterate over group names of the groups defined in this backend.
        """
        return (self.mapper_from_backend(group_name) for group_name in self._backend)

    def __contains__(self, group_name):
        """
        Check if a group called group_name is available in this backend.

        @param group_name: name of the group [unicode]
        """
        return self.mapper_to_backend(group_name) in self._backend

    def membergroups(self, member):
        """
        List all group names of the groups where <member> is a member of.

        @param member: member name [unicode]
        @return: list of group names [unicode]
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
