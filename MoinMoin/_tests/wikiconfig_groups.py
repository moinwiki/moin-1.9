# -*- coding: iso-8859-1 -*-
"""
MoinMoin.groups related configuration is defined here.

@copyright: 2009 by MoinMoin:DmitrijsMilajevs
@license: GNU GPL, see COPYING for details.
"""

from wikiconfig import LocalConfig
from MoinMoin.groups import WikiGroups
from MoinMoin.datastruct.dicts import WikiDicts

class Config(LocalConfig):
    group_manager_init = lambda self, request: WikiGroups(request)

    def dict_manager_init(self, request):
        dicts = WikiDicts(request)
        dicts.load_dicts()
        return dicts
