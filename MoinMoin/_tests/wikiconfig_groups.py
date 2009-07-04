# -*- coding: iso-8859-1 -*-
"""
MoinMoin.groups related configuration is defined here.

@copyright: 2009 by MoinMoin:DmitrijsMilajevs
@license: GNU GPL, see COPYING for details.
"""

from wikiconfig import LocalConfig
from MoinMoin.datastruct import WikiGroups, WikiDicts

class Config(LocalConfig):
    group_manager_init = lambda self, request: WikiGroups(request)
    dict_manager_init = lambda self, request: WikiDicts(request)

