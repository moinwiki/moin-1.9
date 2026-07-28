# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.action.info Tests

    @copyright: 2026 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin._tests import become_trusted, create_page, nuke_page, wikiconfig


class TestInfoViews:
    """ only the revision history is left of what info used to show """

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

    def test_retired_views_are_not_served(self):
        assert self._get(hitcounts=1)[0] == '404'
        assert self._get(general=1)[0] == '404'

    def test_retired_views_are_not_served_whatever_they_say(self):
        # the values are not parsed at all, so this can not be an unhandled
        # ValueError (which is what an unparsable one used to be)
        for value in ('0', 'abc', ''):
            for view in ('hitcounts', 'general'):
                status = self._get(**{view: value})[0]
                assert status == (value and '404' or '200')

    def test_retired_views_are_not_offered(self):
        status, body = self._get()
        assert status == '200'
        assert 'hitcounts' not in body
        assert 'general' not in body

    def test_the_history_is_still_served(self):
        status, body = self._get()
        assert status == '200'
        # the history listing, not an empty frame
        assert 'info-paging-info' in body or 'Editor' in body


coverage_modules = ['MoinMoin.action.info']
