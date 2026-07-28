# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.action.info Tests

    @copyright: 2026 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin._tests import become_trusted, create_page, nuke_page, wikiconfig


class TestInfoViews:
    """ the page hits and edits view is gone, the others still work """

    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForInfo'

    class Config(wikiconfig.Config):
        # we do a bunch of requests in a row here, they must be answered by
        # the wiki and not by the surge protection
        surge_action_limits = None

    def setup_class(self):
        become_trusted(self.request)
        create_page(self.request, self.pagename, u"a page with some info")

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _get(self, **query):
        query['action'] = 'info'
        appiter, status, headers = self.client.get('/%s' % self.pagename,
                                                   query_string=query)
        return status[:3], ''.join(appiter)

    def test_hitcounts_is_not_served(self):
        status, body = self._get(hitcounts=1)
        assert status == '404'

    def test_hitcounts_is_not_served_whatever_it_says(self):
        # the value is not parsed at all, so this can not be an unhandled
        # ValueError (which is what an unparsable one used to be)
        for value in ('0', 'abc', ''):
            status, body = self._get(hitcounts=value)
            assert status == (value and '404' or '200')

    def test_hitcounts_is_not_offered(self):
        status, body = self._get()
        assert status == '200'
        assert 'hitcounts' not in body

    def test_other_views_still_work(self):
        status, body = self._get()
        assert status == '200'
        status, body = self._get(general=1)
        assert status == '200'


coverage_modules = ['MoinMoin.action.info']
