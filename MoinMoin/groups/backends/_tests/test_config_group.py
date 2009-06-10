# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.groups.backends.wiki_group tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2008 by MoinMoin:MelitaMihaljevic
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.

"""

from  MoinMoin.groups.backends._tests import BackendTest, BackendTestMapping, Config
from MoinMoin.groups.backends import config_group
from MoinMoin.groups import GroupManager

class TestConfigBackend(BackendTest):

    class Config(Config):
        def group_manager_init(self, request):
            self.config_groups = BackendTest.test_groups
            return GroupManager(backends=[config_group.Backend(request)])

class TestConfigBackendMapping(TestConfigBackend):

    class Config(Config):
        def group_manager_init(self, request):
            backend = config_group.Backend(request, TestConfigBackend.mapped_groups)

            backend.to_backend_name = self.to_backend_name
            backend.to_group_name = self.to_group_name

            return GroupManager(backends=[backend])

coverage_modules = ['MoinMoin.groups.backends.config_group']

