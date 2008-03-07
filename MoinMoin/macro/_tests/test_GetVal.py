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
from MoinMoin._tests.common import gain_superuser_rights

class TestGetVal:
    """GetVal: testing getVal macro """

        # injected for you into the test class by moin test framework.
    def setup_method(self, method):
        gain_superuser_rights(self.request)
        self.cfg = self.request.cfg
        self.pagename = u'MyDict'
        self.page = PageEditor(self.request, self.pagename, do_editor_backup=0)
        self.shouldDeleteTestPage = True

        # for that test eventlog needs to be empty
        fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
        if os.path.exists(fpath):
            os.remove(fpath)


    def teardown_method(self, method):
        if self.shouldDeleteTestPage:
            page = PageEditor(self.request, self.pagename, do_editor_backup=0)
            success_i, msg = page.deletePage()

            fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
            if os.path.exists(fpath):
                os.remove(fpath)


    def _make_macro(self):
        """Test helper"""
        from MoinMoin.parser.text import Parser
        from MoinMoin.formatter.text_html import Formatter
        p = Parser("##\n", self.request)
        p.formatter = Formatter(self.request)
        p.formatter.page = self.page
        self.request.formatter = p.formatter
        p.form = self.request.form
        m = macro.Macro(p)
        return m

    def _test_macro(self, name, args):
        m = self._make_macro()
        return m.execute(name, args)

    def _createTestPage(self, body):
        """ Create temporary page """
        assert body is not None

        self.request.reset()
        try:
            self.page.saveText(body, 0)
        except:
            pass

    def testGetValNoACLs(self):
        """ macro GetVal test: 'reads VAR' """

        self.shouldDeleteTestPage = True
        self._createTestPage(u' VAR:: This is an example')

        page = Page(self.request, self.pagename)
        args = "%s,%s" % (self.pagename, u'VAR')
        result = self._test_macro(u'GetVal', args)

        expected = "This is an example"
        assert result == expected

    def testGetValAfterADictPageIsDeleted(self):
        """ macro GetVal test: 'reads Dict var after another Dict is removed' """

        self.shouldDeleteTestPage = True

        pagename = u'SomeDict'
        page = PageEditor(self.request, pagename, do_editor_backup=0)
        body = u" EXAMPLE:: This is an example text"
        try:
            page.saveText(body, 0)
        except:
            pass
        success_i, result = page.deletePage()

        self._createTestPage(u' VAR:: This is a brand new example')
        page = Page(self.request, self.pagename)
        args = "%s,%s" % (self.pagename, u'VAR')
        result = self._test_macro(u'GetVal', args)

        expected = "This is a brand new example"
        assert result == expected

    def testGetValACLs(self):
        """ macro GetVal test: 'cant read VAR on an ACL protected page' """
        py.test.skip("user has no rights to create acl pages")
        self.shouldDeleteTestPage = True
        self._createTestPage('#acl SomeUser:read,write All:delete\n VAR:: This is an example')
        args = "%s,%s" % (self.pagename, u'VAR')
        result = self._test_macro(u'GetVal', args)
        expected = "&lt;&lt;GetVal: You don't have enough rights on this page&gt;&gt;"
        assert result == expected

coverage_modules = ['MoinMoin.macro.GetVal']

