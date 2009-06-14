# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.groups.backends.wiki_group tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2008 by MoinMoin:MelitaMihaljevic
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.

"""

from  MoinMoin.groups.backends._tests import BackendTest
from MoinMoin.groups import ConfigGroups
from MoinMoin._tests import wikiconfig


class TestConfigBackend(BackendTest):

    class Config(wikiconfig.Config):

        def group_manager_init(self, request):
            groups = BackendTest.test_groups
            return ConfigGroups(request, groups)


coverage_modules = ['MoinMoin.groups.backends.config_groups']

