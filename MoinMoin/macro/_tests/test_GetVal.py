# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro GetVal tested

    @copyright: 2007 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""
import os, py

from MoinMoin import macro
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin._tests import become_trusted, create_page, make_macro, nuke_page

class TestGetVal:
    """GetVal: testing getVal macro """
    pagename = u'MyDict'

    def setup_class(self):
        become_trusted(self.request)
        self.cfg = self.request.cfg

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _test_macro(self, name, args):
        m = make_macro(self.request, self.page)
        return m.execute(name, args)

    def testGetValNoACLs(self):
        """ macro GetVal test: 'reads VAR' """
        self.page = create_page(self.request, self.pagename, u' VAR:: This is an example')
        result = self._test_macro(u'GetVal', "%s,%s" % (self.pagename, u'VAR'))
        assert result == "This is an example"

    def testGetValAfterADictPageIsDeleted(self):
        """ macro GetVal test: 'reads Dict var after another Dict is removed' """
        request = self.request
        page = create_page(request, u'SomeDict', u" EXAMPLE:: This is an example text")
        page.deletePage()
        page = create_page(request, self.pagename, u' VAR:: This is a brand new example')
        result = self._test_macro(u'GetVal', "%s,%s" % (self.pagename, u'VAR'))
        nuke_page(request, u'SomeDict')
        assert result == "This is a brand new example"

    def testGetValACLs(self):
        """ macro GetVal test: 'cant read VAR on an ACL protected page' """
        py.test.skip("user has no rights to create acl pages")
        self.page = create_page(self.request, self.pagename,
                                '#acl SomeUser:read,write All:delete\n VAR:: This is an example')
        result = self._test_macro(u'GetVal', "%s,%s" % (self.pagename, u'VAR'))
        assert result == "&lt;&lt;GetVal: You don't have enough rights on this page&gt;&gt;"

coverage_modules = ['MoinMoin.macro.GetVal']

