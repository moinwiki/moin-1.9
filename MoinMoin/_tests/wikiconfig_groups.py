# -*- coding: iso-8859-1 -*-
"""
MoinMoin.groups related configuration is defined here.

@copyright: 2009 by MoinMoin:DmitrijsMilajevs
@license: GNU GPL, see COPYING for details.
"""

from wikiconfig import LocalConfig
from MoinMoin.groups import GroupManager
from MoinMoin.groups.backends import wiki_group

class Config(LocalConfig):
    group_manager_init = lambda self, request: GroupManager([wiki_group.Backend(request)])

