# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro StatsChart tested

    @copyright: 2008 MoinMoin:ReimarBauer

    @license: GNU GPL, see COPYING for details.
"""
import os

from MoinMoin import caching, macro
from MoinMoin.logfile import eventlog
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page
from MoinMoin._tests import become_trusted

class TestStatsCharts:
    """StartsChart: testing StatsChart macro """

    def setup_class(self):
        self.pagename = u'AutoCreatedMoinMoinTemporaryTestPageStatsChart'
        self.page = PageEditor(self.request, self.pagename)
        self.shouldDeleteTestPage = False
        become_trusted(self.request)
        # clean page scope cache entries
        keys = ['text_html', 'pagelinks', ]
        arena = Page(self.request, self.pagename)
        for key in keys:
            caching.CacheEntry(self.request, arena, key, scope='item').remove()

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
        self.request.page = self.page
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
        except self.page.Unchanged:
            pass

    def testStatsChart_useragents(self):
        """ macro StatsChart useragents test: 'tests useragents' and clean page scope cache """
        self.shouldDeleteTestPage = True
        self._createTestPage('This is an example to test useragents from StatsChart macro without page cache')

        result = self._test_macro(u'StatsChart', u'useragents')
        expected = u'<form action="./AutoCreatedMoinMoinTemporaryTestPageStatsChart" method="GET"'
        assert expected in result

    def testStatsChart_hitcounts(self):
        """ macro StatsChart hitcounts test: 'tests hitcounts' and clean page scope cache  """
        self.shouldDeleteTestPage = True
        self._createTestPage('This is an example to test hitcounts from StatsChart macro without page cache')

        result = self._test_macro(u'StatsChart', u'hitcounts')
        expected = u'<form action="./AutoCreatedMoinMoinTemporaryTestPageStatsChart" method="GET"'
        assert expected in result

    def testStatsChart_languages(self):
        """ macro StatsChart languages test: 'tests languages' and clean page scope cache  """
        self.shouldDeleteTestPage = True
        self._createTestPage('This is an example to test languages from StatsChart macro without page cache')

        result = self._test_macro(u'StatsChart', u'hitcounts')
        expected = u'<form action="./AutoCreatedMoinMoinTemporaryTestPageStatsChart" method="GET"'
        assert expected in result

coverage_modules = ['MoinMoin.stats']

