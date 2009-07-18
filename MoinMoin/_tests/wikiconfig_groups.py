# -*- coding: iso-8859-1 -*-
"""
MoinMoin.groups related configuration is defined here.

@copyright: 2009 by MoinMoin:DmitrijsMilajevs
@license: GNU GPL, see COPYING for details.
"""

from wikiconfig import LocalConfig
from MoinMoin.datastruct import WikiGroups, WikiDicts

class Config(LocalConfig):
    groups = lambda self, request: WikiGroups(request)
    dicts = lambda self, request: WikiDicts(request)

