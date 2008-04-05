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
from MoinMoin._tests.common import gain_superuser_rights

class TestHits:
    """Hits: testing Hits macro """

    def setup_class(self):
        gain_superuser_rights(self.request)
        self.pagename = u'AutoCreatedMoinMoinTemporaryTestPageForPageHits'
        self.page = PageEditor(self.request, self.pagename)
        self.shouldDeleteTestPage = True
        # for that test eventlog needs to be empty
        fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
        if os.path.exists(fpath):
            os.remove(fpath)
        # hits is based on hitcounts which reads the cache
        caching.CacheEntry(self.request, 'charts', 'pagehits', scope='wiki').remove()
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

    def testPageHits(self):
        """ macro PageHits test: updating of cache from event-log for multiple call of PageHits"""
        self.shouldDeleteTestPage = True
        self._createTestPage('This is an example to test a macro')

        # Three log entries for the current page and one for WikiSandBox simulating viewing
        for counter in range(20):
            eventlog.EventLog(self.request).add(self.request, 'VIEWPAGE', {'pagename': 'PageHits'})
            result = self._test_macro(u'PageHits', u'')

        cache = caching.CacheEntry(self.request, 'charts', 'pagehits', scope='wiki', use_pickle=True)
        date, hits = 0, {}
        if cache.exists():
            try:
                date, hits = cache.content()
            except caching.CacheError:
                cache.remove()
        expected = 20
        assert hits['PageHits'] == expected

coverage_modules = ['MoinMoin.macro.PageHits']

