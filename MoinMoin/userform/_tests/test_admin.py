# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.userform.admin Tests

    @copyright: 2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""


from MoinMoin.userform.admin import do_user_browser
from MoinMoin.datastruct import ConfigGroups
from MoinMoin.user import User
from MoinMoin.Page import Page
from MoinMoin._tests import nuke_user, become_superuser, wikiconfig

class TestAdmin:

    class Config(wikiconfig.Config):

        def groups(self, request):
            groups = {'OneGroup': ['TestUser, OtherUser'],
                      'OtherGroup': ['TestUser']}
            return ConfigGroups(request, groups)

    def setup_class(self):
        request = self.request
        user_name = 'TestUser'
        self.user_name = user_name

        become_superuser(request)

        User(request, name=user_name, password=user_name).save()

    def teardown_class(self):
        nuke_user(self.request, self.user_name)

    def setup_method(self, method):
        self.request.page = Page(self.request, 'SystemAdmin')

    def test_do_user_browser(self):
        request = self.request

        browser = do_user_browser(request)
        assert browser


coverage_modules = ['MoinMoin.userform.admin']

