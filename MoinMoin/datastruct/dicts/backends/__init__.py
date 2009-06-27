# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.datastruct.dicts.backends.

    @copyright: 2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""


class DictDoesNotExistError(Exception):
    """
    Raised when a dict name is not found in the backend.
    """


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
        return self._backend._retrieve_members(self.name)

    def __repr__(self):
        return "<%r name=%r items=%r>" % (self.__class__, self.name, self._dict.items())


class BaseDictBackend(object):

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

    def _retrieve_members(self, dict_name):
        raise NotImplementedError()

