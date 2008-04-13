# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro Hits tested

    @copyright: 2007-2008 MoinMoin:ReimarBauer
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
        # for that test eventlog needs to be empty
        fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
        if os.path.exists(fpath):
            os.remove(fpath)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(self.request, 'charts', 'hitcounts', scope='wiki').remove()
        arena = Page(self.request, self.pagename)
        caching.CacheEntry(self.request, arena, 'hitcounts', scope='item').remove()

    def teardown_class(self):
        import shutil
        page = PageEditor(self.request, self.pagename)
        fpath = page.getPagePath(use_underlay=0, check_create=0)
        shutil.rmtree(fpath, True)

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

    def _cleanStats(self):
        # cleans all involved cache and log files
        fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
        if os.path.exists(fpath):
            os.remove(fpath)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(self.request, 'charts', 'hitcounts', scope='wiki').remove()
        arena = Page(self.request, self.pagename)
        caching.CacheEntry(self.request, arena, 'hitcounts', scope='item').remove()

    def testHitsNoArg(self):
        """ macro Hits test: 'no args for Hits (Hits is executed on current page) """
        # Three log entries for the current page and one for WikiSandBox simulating viewing
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'WikiSandBox'})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})

        result = self._test_macro(u'Hits', u'')
        self._cleanStats()
        expected = "3"
        assert result == expected

    def testHitsForAll(self):
        """ macro Hits test: 'all=True' for Hits (all pages are counted for VIEWPAGE) """
        # Two log entries for simulating viewing
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'WikiSandBox'})
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'WikiSandBox'})

        result = self._test_macro(u'Hits', u'all=True')
        self._cleanStats()
        expected = "4"
        assert result == expected

    def testHitsForFilter(self):
        """ macro Hits test: 'event_type=SAVEPAGE' for Hits (SAVEPAGE counted for current page)"""
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': self.pagename})
        # simulate a log entry SAVEPAGE for WikiSandBox to destinguish current page
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': 'WikiSandBox'})

        result = self._test_macro(u'Hits', u'event_type=SAVEPAGE')
        self._cleanStats()
        expected = "1"
        assert result == expected

    def testHitsForAllAndFilter(self):
        """ macro test: 'all=True, event_type=SAVEPAGE' for Hits (all pages are counted for SAVEPAGE)"""
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': 'WikiSandBox'})
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': self.pagename})

        result = self._test_macro(u'Hits', u'all=True, event_type=SAVEPAGE')
        self._cleanStats()
        expected = "2"
        assert result == expected


coverage_modules = ['MoinMoin.macro.Hits']

