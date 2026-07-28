# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.action.diff Tests

    @copyright: 2026 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.action import diff
from MoinMoin.Page import Page
from MoinMoin._tests import become_trusted, create_page, append_page, nuke_page, wikiconfig


class TestComparableRevisions:
    """ only the diffs we offer a way to reach are served """

    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForDiff'
    revisions = 30 # enough to have revisions outside of the recent ones

    class Config(wikiconfig.Config):
        # we do a bunch of requests in a row here, they must be answered by
        # the wiki and not by the surge protection
        surge_action_limits = None

    def setup_class(self):
        become_trusted(self.request)
        create_page(self.request, self.pagename, u"revision 1")
        for rev in range(2, self.revisions + 1):
            append_page(self.request, self.pagename, u"revision %d" % rev)
        assert Page(self.request, self.pagename).current_rev() == self.revisions

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _status(self, **query):
        query['action'] = 'diff'
        appiter, status, headers = self.client.get('/%s' % self.pagename,
                                                   query_string=query)
        ''.join(appiter) # consume it, we only care about the status
        return status[:3]

    def test_recent_revisions_may_be_compared(self):
        # the most recent DIFF_RECENT_REVS revisions, any two of them
        oldest_recent = self.revisions - diff.DIFF_RECENT_REVS + 1
        assert self._status(rev1=self.revisions - 1, rev2=self.revisions) == '200'
        assert self._status(rev1=oldest_recent, rev2=self.revisions) == '200'
        assert self._status(rev1=oldest_recent, rev2=oldest_recent + 1) == '200'

    def test_nearby_revisions_may_be_compared(self):
        # old ones, too, as long as they do not span much
        assert self._status(rev1=1, rev2=2) == '200'
        assert self._status(rev1=1, rev2=1 + diff.DIFF_MAX_SPAN) == '200'
        assert self._status(rev1=3, rev2=3 + diff.DIFF_MAX_SPAN) == '200'

    def test_old_and_far_apart_is_forbidden(self):
        oldest_recent = self.revisions - diff.DIFF_RECENT_REVS + 1
        # one revision older than the recent ones and spanning more than
        # DIFF_MAX_SPAN is enough to be refused
        assert self._status(rev1=oldest_recent - 1, rev2=self.revisions) == '403'
        assert self._status(rev1=1, rev2=2 + diff.DIFF_MAX_SPAN) == '403'
        assert self._status(rev1=1, rev2=self.revisions) == '403'

    def test_defaults_are_served(self):
        # no revisions given: current against the one before it
        assert self._status() == '200'
        assert self._status(rev1=self.revisions - 1) == '200'


coverage_modules = ['MoinMoin.action.diff']
