# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro PageHits tested

    @copyright: 2008 MoinMoin:ReimarBauer
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
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForPageHits'

    def setup_class(self):
        request = self.request
        become_trusted(request)
        self.page = create_page(request, self.pagename, u"Foo!")
        # for that test eventlog needs to be empty
        nuke_eventlog(self.request)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(request, 'charts', 'pagehits', scope='wiki').remove()
        caching.CacheEntry(request, 'charts', 'hitcounts', scope='wiki').remove()

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _test_macro(self, name, args):
        m = make_macro(self.request, self.page)
        return m.execute(name, args)

    def testPageHits(self):
        """ macro PageHits test: updating of cache from event-log for multiple call of PageHits"""
        count = 20
        for counter in range(count):
            eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'PageHits'})
            result = self._test_macro(u'PageHits', u'') # XXX SENSE???
        cache = caching.CacheEntry(self.request, 'charts', 'pagehits', scope='wiki', use_pickle=True)
        date, hits = 0, {}
        if cache.exists():
            try:
                date, hits = cache.content()
            except caching.CacheError:
                cache.remove()
        assert hits['PageHits'] == count

coverage_modules = ['MoinMoin.macro.PageHits']
