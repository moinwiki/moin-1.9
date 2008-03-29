# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro Hits tested

    @copyright: 2007 MoinMoin:ReimarBauer

    @license: GNU GPL, see COPYING for details.
"""
import os

from MoinMoin import caching, macro
from MoinMoin.logfile import eventlog
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page

class TestHits:
    """Hits: testing Hits macro """

    def setup_class(self):
        self.pagename = u'AutoCreatedMoinMoinTemporaryTestPageForHits'
        self.page = PageEditor(self.request, self.pagename)
        self.shouldDeleteTestPage = False
        # for that test eventlog needs to be empty
        fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
        if os.path.exists(fpath):
            os.remove(fpath)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(self.request, 'charts', 'hitcounts', scope='wiki').remove()
        arena = Page(self.request, self.pagename)
        caching.CacheEntry(self.request, arena, 'hitcounts', scope='item').remove()

    def teardown_class(self):
        if self.shouldDeleteTestPage:
            import shutil
            page = PageEditor(self.request, self.pagename)
            page.deletePage()
            fpath = page.getPagePath(use_underlay=0, check_create=0)
            shutil.rmtree(fpath, True)

        fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
        if os.path.exists(fpath):
            os.remove(fpath)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(self.request, 'charts', 'hitcounts', scope='wiki').remove()
        arena = Page(self.request, self.pagename)
        caching.CacheEntry(self.request, arena, 'hitcounts', scope='item').remove()

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

    def testHitsNoArg(self):
        """ macro Hits test: 'no args for Hits (Hits is executed on current page) """
        self.shouldDeleteTestPage = False
        self._createTestPage('This is an example to test a macro')

        # Three log entries for the current page and one for WikiSandBox simulating viewing
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'WikiSandBox'})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})

        result = self._test_macro(u'Hits', u'')
        expected = "3"
        assert result == expected

    def testHitsForAll(self):
        """ macro Hits test: 'all=True' for Hits (all pages are counted for VIEWPAGE) """
        self.shouldDeleteTestPage = False
        self._createTestPage('This is an example to test a macro with parameters')

        # Two log entries for simulating viewing
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})

        result = self._test_macro(u'Hits', u'all=True')
        expected = "6"
        assert result == expected

    def testHitsForFilter(self):
        """ macro Hits test: 'all=True, event_type=SAVEPAGE' for Hits (SAVEPAGE counted for current page)"""
        self.shouldDeleteTestPage = False

        # simulate a log entry SAVEPAGE for WikiSandBox to destinguish current page
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': 'WikiSandBox'})
        result = self._test_macro(u'Hits', u'event_type=SAVEPAGE')
        expected = "2"
        assert result == expected

    def testHitsForAllAndFilter(self):
        """ macro test: 'all=True, event_type=SAVEPAGE' for Hits (all pages are counted for SAVEPAGE)"""
        self.shouldDeleteTestPage = True

        result = self._test_macro(u'Hits', u'all=True, event_type=SAVEPAGE')
        expected = "3"
        assert result == expected


coverage_modules = ['MoinMoin.macro.Hits']

