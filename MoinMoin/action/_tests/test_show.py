# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.action show Tests

    @copyright: 2026 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import time

from MoinMoin import action
from MoinMoin._tests import become_trusted, create_page, nuke_page, wikiconfig


class TestDatePages:
    """ day pages of a calendar with an implausible year are not rendered """

    basename = u'AutoCreatedMoinMoinTemporaryTestPageForShow'

    class Config(wikiconfig.Config):
        # we do a bunch of requests in a row here, they must be answered by
        # the wiki and not by the surge protection
        surge_action_limits = None

    def setup_class(self):
        become_trusted(self.request)
        create_page(self.request, self.basename, u"a calendar lives here")
        # a day page far away from now, but written on purpose
        self.existing = u'%s/1234-05-06' % self.basename
        create_page(self.request, self.existing, u"something worth keeping")

    def teardown_class(self):
        nuke_page(self.request, self.existing)
        nuke_page(self.request, self.basename)

    def _status(self, pagename):
        appiter, status, headers = self.client.get('/%s' % pagename)
        ''.join(appiter) # consume it, we only care about the status
        return status[:3]

    def test_nearby_day_pages_are_shown(self):
        year = time.localtime()[0]
        for offset in (0, action.DATE_PAGE_MAX_YEARS, -action.DATE_PAGE_MAX_YEARS):
            # nonexisting, so this is the usual "does not exist" 404
            assert self._status(u'%s/%d-07-14' % (self.basename, year + offset)) == '404'

    def test_far_away_day_pages_are_forbidden(self):
        year = time.localtime()[0]
        far = (year + action.DATE_PAGE_MAX_YEARS + 1,
               year - action.DATE_PAGE_MAX_YEARS - 1,
               9999, 1)
        for y in far:
            assert self._status(u'%s/%04d-07-14' % (self.basename, y)) == '403'
        # an implausibly long year does not even get its int() computed
        assert self._status(u'%s/123456789-07-14' % self.basename) == '403'

    def test_existing_far_away_day_page_is_shown(self):
        # it is real content, no matter how far away its name points
        assert self._status(self.existing) == '200'

    def test_other_pages_are_untouched(self):
        # not a day page at all
        assert self._status(u'%s/NoSuchSubPage' % self.basename) == '404'
        assert self._status(self.basename) == '200'
        # the anniversary naming of MonthCalendar has no year in it
        assert self._status(u'%s/07-14' % self.basename) == '404'


coverage_modules = ['MoinMoin.action']
