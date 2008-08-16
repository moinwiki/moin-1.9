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
from MoinMoin._tests import become_trusted, create_page, make_macro, nuke_eventlog, nuke_page

class TestHits:
    """Hits: testing Hits macro """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForHits'

    def setup_class(self):
        request = self.request
        become_trusted(request)
        self.page = create_page(request, self.pagename, u"Foo!")
        # for that test eventlog needs to be empty
        nuke_eventlog(request)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(request, 'charts', 'hitcounts', scope='wiki').remove()

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _test_macro(self, name, args):
        m = make_macro(self.request, self.page)
        return m.execute(name, args)

    def _cleanStats(self):
        # cleans all involved cache and log files
        nuke_eventlog(self.request)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(self.request, 'charts', 'hitcounts', scope='wiki').remove()
        arena = Page(self.request, self.pagename)
        caching.CacheEntry(self.request, arena, 'hitcounts', scope='item').remove()

    def testHitsNoArg(self):
        """ macro Hits test: 'no args for Hits (Hits is executed on current page) """
        # <count> log entries for the current page and one for WikiSandBox simulating viewing
        count = 3
        eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'WikiSandBox'})
        for i in range(count):
            eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': self.pagename})
        result = self._test_macro(u'Hits', u'')
        self._cleanStats()
        assert result == str(count)

    def testHitsForAll(self):
        """ macro Hits test: 'all=True' for Hits (all pages are counted for VIEWPAGE) """
        # <count> * <num_pages> log entries for simulating viewing
        pagenames = ['WikiSandBox', self.pagename]
        num_pages = len(pagenames)
        count = 2
        for i in range(count):
            for pagename in pagenames:
                eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': pagename})
        result = self._test_macro(u'Hits', u'all=True')
        self._cleanStats()
        assert result == str(count * num_pages)

    def testHitsForFilter(self):
        """ macro Hits test: 'event_type=SAVEPAGE' for Hits (SAVEPAGE counted for current page)"""
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': self.pagename})
        # simulate a log entry SAVEPAGE for WikiSandBox to destinguish current page
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': 'WikiSandBox'})
        result = self._test_macro(u'Hits', u'event_type=SAVEPAGE')
        self._cleanStats()
        assert result == "1"

    def testHitsForAllAndFilter(self):
        """ macro test: 'all=True, event_type=SAVEPAGE' for Hits (all pages are counted for SAVEPAGE)"""
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': 'WikiSandBox'})
        eventlog.EventLog(self.request).add(self.request, 'SAVEPAGE', {'pagename': self.pagename})
        result = self._test_macro(u'Hits', u'all=True, event_type=SAVEPAGE')
        self._cleanStats()
        assert result == "2"

coverage_modules = ['MoinMoin.macro.Hits']
