# -*- coding: iso-8859-1 -*-
"""
MoinMoin - MoinMoin.wikisync tests

@copyright: 2006 MoinMoin:AlexanderSchremmer
@license: GNU GPL, see COPYING for details.
"""

from unittest import TestCase
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin._tests import TestConfig, TestSkipped

from MoinMoin.wikisync import TagStore, BOTH


class UnsafeSyncTestcase(TestCase):
    """ Tests various things related to syncing. Note that it is not possible
        to create pages without cluttering page revision currently, so we have to use
        the testwiki. """

    def setUp(self):
        if not getattr(self.request.cfg, 'is_test_wiki', False):
            raise TestSkipped('This test needs to be run using the test wiki.')
        self.page = PageEditor(self.request, "FrontPage")

    def testBasicTagThings(self):
        tags = TagStore(self.page)
        self.assert_(not tags.get_all_tags())
        tags.add(remote_wiki="foo", remote_rev=1, current_rev=2, direction=BOTH)
        tags = TagStore(self.page) # reload
        self.assert_(tags.get_all_tags()[0].remote_rev == 1)
    
    def tearDown(self):
        tags = TagStore(self.page)
        tags.clear()
