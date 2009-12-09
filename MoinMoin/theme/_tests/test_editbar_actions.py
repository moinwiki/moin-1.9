# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.theme Tests

    @copyright: 2008 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.theme import ThemeBase
from MoinMoin.Page import Page

class TestEditBarActions(object):
    def setup_method(self, method):
        self.savedValid = self.request.user.valid
        self.savedMailEnabled = self.request.cfg.mail_enabled
        self.request.cfg.mail_enabled = True
        self.page = Page(self.request, u'FrontPage')
        self.ThemeBase = ThemeBase(self.request)

    def teardown_method(self, method):
        self.request.user.valid = self.savedValid
        self.request.cfg.mail_enabled = self.savedMailEnabled

    def test_editbar_for_anonymous_user(self):
        assert not self.request.user.valid
        assert not self.ThemeBase.subscribeLink(self.page)
        assert not self.ThemeBase.quicklinkLink(self.page)

    def test_editbar_for_valid_user(self):
        self.request.user.valid = True
        assert self.request.user.valid
        assert 'subscribe' in self.ThemeBase.subscribeLink(self.page)
        assert 'quicklink' in self.ThemeBase.quicklinkLink(self.page)

coverage_modules = ['MoinMoin.theme']
