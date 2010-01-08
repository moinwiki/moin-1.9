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
from MoinMoin._tests import become_trusted, create_page, make_macro, nuke_page

class TestStatsCharts:
    """StartsChart: testing StatsChart macro """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageStatsChart'

    def setup_class(self):
        become_trusted(self.request)
        self.page = create_page(self.request, self.pagename, u"Foo!")
        # clean page scope cache entries
        for key in ['text_html', 'pagelinks', ]:
            caching.CacheEntry(self.request, self.page, key, scope='item').remove()

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _test_macro(self, name, args):
        m = make_macro(self.request, self.page)
        return m.execute(name, args)

    def testStatsChart_useragents(self):
        """ macro StatsChart useragents test: 'tests useragents' and clean page scope cache """
        result = self._test_macro(u'StatsChart', u'useragents')
        expected = u'<form action="/AutoCreatedMoinMoinTemporaryTestPageStatsChart" method="GET"'
        assert expected in result

    def testStatsChart_hitcounts(self):
        """ macro StatsChart hitcounts test: 'tests hitcounts' and clean page scope cache  """
        result = self._test_macro(u'StatsChart', u'hitcounts')
        expected = u'<form action="/AutoCreatedMoinMoinTemporaryTestPageStatsChart" method="GET"'
        assert expected in result

    def testStatsChart_languages(self):
        """ macro StatsChart languages test: 'tests languages' and clean page scope cache  """
        result = self._test_macro(u'StatsChart', u'hitcounts')
        expected = u'<form action="/AutoCreatedMoinMoinTemporaryTestPageStatsChart" method="GET"'
        assert expected in result

coverage_modules = ['MoinMoin.stats']
