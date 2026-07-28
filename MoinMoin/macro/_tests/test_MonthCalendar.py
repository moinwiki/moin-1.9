# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro.MonthCalendar Tests

    @copyright: 2026 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import time

from MoinMoin.macro import MonthCalendar
from MoinMoin._tests import become_trusted, create_page, nuke_page, wikiconfig


class TestOffsetCalculation:
    """ the arithmetic, no request needed """

    def test_yearmonthplusoffset(self):
        f = MonthCalendar.yearmonthplusoffset
        assert f(2010, 1, 0) == (2010, 1)
        assert f(2010, 12, 1) == (2011, 1)
        assert f(2010, 1, -1) == (2009, 12)
        assert f(2010, 6, 12) == (2011, 6)
        assert f(2010, 6, -12) == (2009, 6)
        assert f(2010, 1, 25) == (2012, 2)
        assert f(2010, 1, -25) == (2007, 12)
        # an offset comes from the url, so a big one must be computed,
        # not looped towards
        assert f(2010, 1, 12 * 10 ** 12) == (2010 + 10 ** 12, 1)

    def test_monthsbetween(self):
        d = MonthCalendar.monthsbetween
        assert d(2010, 1, 2010, 1) == 0
        assert d(2010, 2, 2010, 1) == 1
        assert d(2009, 12, 2010, 1) == -1
        assert d(2011, 1, 2010, 1) == 12
        assert d(2009, 1, 2010, 1) == -12
        # inverse of yearmonthplusoffset
        for offset in (-30, -1, 0, 1, 30):
            year, month = MonthCalendar.yearmonthplusoffset(2010, 7, offset)
            assert d(year, month, 2010, 7) == offset


class TestNavigationRange:
    """ months far away from the current one are not rendered on request """

    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForMonthCalendar'

    class Config(wikiconfig.Config):
        # we do a bunch of requests in a row here, they must be answered by
        # the wiki and not by the surge protection
        surge_action_limits = None

    def setup_class(self):
        become_trusted(self.request)
        self.page = create_page(self.request, self.pagename, u"<<MonthCalendar>>")

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _status(self, offset2):
        """ request the test page, navigated by <offset2> months """
        year, month = self.request.user.getTime(time.time())[:2]
        calparms = u'%s,%d,%d,0,%d,,,' % (self.pagename, year, month, offset2)
        appiter, status, headers = self.client.get('/%s' % self.pagename,
                                                   query_string={'calparms': calparms})
        ''.join(appiter) # consume it, we only care about the status
        return status[:3]

    def test_within_range_is_rendered(self):
        maxoffset = MonthCalendar.MAX_NAV_OFFSET
        for offset2 in (0, 1, -1, maxoffset, -maxoffset):
            assert self._status(offset2) == '200'

    def test_out_of_range_is_forbidden(self):
        maxoffset = MonthCalendar.MAX_NAV_OFFSET
        for offset2 in (maxoffset + 1, -(maxoffset + 1), 1200, 10 ** 15):
            assert self._status(offset2) == '403'

    def test_no_calparms_is_rendered(self):
        appiter, status, headers = self.client.get('/%s' % self.pagename)
        ''.join(appiter)
        assert status[:3] == '200'


coverage_modules = ['MoinMoin.macro.MonthCalendar']
