# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.backends.wiki_group tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2008 by MoinMoin:MelitaMihaljevic
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.

"""

from MoinMoin.datastruct.backends._tests import GroupsBackendTest
from MoinMoin.datastruct import ConfigGroups
from MoinMoin._tests import wikiconfig


class TestConfigGroupsBackend(GroupsBackendTest):

    class Config(wikiconfig.Config):

        def group_manager_init(self, request):
            groups = GroupsBackendTest.test_groups
            return ConfigGroups(request, groups)


coverage_modules = ['MoinMoin.datastruct.backends.config_groups']

