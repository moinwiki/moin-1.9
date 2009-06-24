# -*- coding: iso-8859-1 -*-
"""
MoinMoin - group access via various backends.

@copyright: 2009 DmitrijsMilajevs
@license: GPL, see COPYING for details
"""

from MoinMoin.groups.backends.wiki_groups import WikiGroups
from MoinMoin.groups.backends.config_groups import ConfigGroups
from MoinMoin.groups.backends.composite_groups import CompositeGroups
from MoinMoin.groups.backends import GroupDoesNotExistError

