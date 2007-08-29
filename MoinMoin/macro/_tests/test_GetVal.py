# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro GetVal tested

    @copyright: 2007 MoinMoin:ReimarBauer

    @license: GNU GPL, see COPYING for details.
"""
import os, py
from MoinMoin import macro
from MoinMoin.logfile import eventlog
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.parser.text_moin_wiki import Parser

class TestGetVal:
    """GetVal: testing getVal macro """

    def setup_class(self):
        self.cfg = self.request.cfg
        self.pagename = u'MyDict'
        self.page = PageEditor(self.request, self.pagename)
        self.shouldDeleteTestPage = False
        # for that test eventlog needs to be empty
        fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
        if os.path.exists(fpath):
            os.remove(fpath)
        # remove old pages
        import shutil
        page = Page(self.request, self.pagename)
        fpath = page.getPagePath(use_underlay=0, check_create=0)
        shutil.rmtree(fpath, True)

    def teardown_class(self):
        if self.shouldDeleteTestPage:
            import shutil
            page = Page(self.request, self.pagename)
            fpath = page.getPagePath(use_underlay=0, check_create=0)
            shutil.rmtree(fpath, True)

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
        self.page.saveText(body, 0)

    def testGetValNoACLs(self):
        """ macro GetVal test: 'reads VAR' """
        self.shouldDeleteTestPage = True
        self._createTestPage(u' VAR:: This is an example')
        args = "%s,%s" % (self.pagename, u'VAR')
        result = self._test_macro(u'GetVal', args)
        expected = "This is an example"
        assert result == expected

    def testGetValACLs(self):
        py.test.skip("user has no rights to create acl pages")
        """ macro GetVal test: 'cant read VAR on an ACL protected page' """
        self.shouldDeleteTestPage = True
        self._createTestPage('#acl SomeUser:read,write All:delete\n VAR:: This is an example')
        args = "%s,%s" % (self.pagename, u'VAR')
        result = self._test_macro(u'GetVal', args)
        expected = "&lt;&lt;GetVal: You don't have enough rights on this page&gt;&gt;"
        assert result == expected

coverage_modules = ['MoinMoin.macro.GetVal']

