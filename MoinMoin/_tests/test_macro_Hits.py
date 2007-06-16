# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro Hits tested
    Module names must start with 'test_' to be included in the tests.

    @copyright: 2007 MoinMoin:ReimarBauer

    @license: GNU GPL, see COPYING for details.
"""
import os, py, unittest
from StringIO import StringIO
from MoinMoin import macro
from MoinMoin.logfile import eventlog
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.parser.text_moin_wiki import Parser

class TestHits(unittest.TestCase):
    """Hits: testing Hits macro """

    pagename = u'AutoCreatedMoinMoinTemporaryTestPage'

    def setUp(self):
        self.page = PageEditor(self.request, self.pagename)

    def tearDown(self):
        self.deleteTestPage()

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

    def createTestPage(self, body):
        """ Create temporary page """
        assert body is not None
        self.request.reset()
        self.page.saveText(body, 0)

    def deleteTestPage(self):
        """ Delete temporary page, bypass logs and notifications """
        if self.shouldDeleteTestPage:
            import shutil
            shutil.rmtree(self.getPagePath(), True)

            fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
            if os.path.exists(fpath):
                os.remove(fpath)

    def getPagePath(self):
        page = Page(self.request, self.pagename)
        return page.getPagePath(use_underlay=0, check_create=0)

    def testHitsNoArg(self):
        """ macro Hits test: 'no args for Hits (Hits is executed on current page) """
        self.shouldDeleteTestPage = False
        self.createTestPage('This is an example to test a macro')

        # Three log entries for the current page and one for WikiSandBox simulating viewing
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'WikiSandBox'})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})

        result = self._test_macro('Hits', '')
        expected = "3"
        self.assertEqual(result, expected,
                     '"%s" not in "%s"' % (expected, result))

    def testHitsForAll(self):
        """ macro Hits test: 'all=1' for Hits (all pages are counted for VIEWPAGE) """
        self.shouldDeleteTestPage = False
        self.createTestPage('This is an example to test a macro with parameters')

        # Two log entries for simulating viewing
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})

        result = self._test_macro('Hits', 'all=1')
        expected = "6"
        self.assertEqual(result, expected,
                     '"%s" not in "%s"' % (expected, result))

    def testHitsForFilter(self):
        """ macro Hits test: 'all=1, filter=SAVEPAGE' for Hits (SAVEPAGE counted for current page)"""
        self.shouldDeleteTestPage = False

        # simulate a log entry SAVEPAGE for WikiSandBox to destinguish current page
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': 'WikiSandBox'})
        result = self._test_macro('Hits', 'filter=SAVEPAGE')
        expected = "2"
        self.assertEqual(result, expected,
                     '"%s" not in "%s"' % (expected, result))

    def testHitsForAllAndFilter(self):
        """ macro test: 'all=1, filter=SAVEPAGE' for Hits (all pages are counted for SAVEPAGE)"""
        self.shouldDeleteTestPage = True

        result = self._test_macro('Hits', 'all=1, filter=SAVEPAGE')
        expected = "3"
        self.assertEqual(result, expected,
                     '"%s" not in "%s"' % (expected, result))

