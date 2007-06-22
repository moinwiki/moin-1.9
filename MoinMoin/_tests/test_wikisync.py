# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikisync tests

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from unittest import TestCase # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS

import py

from MoinMoin.PageEditor import PageEditor

from MoinMoin.wikisync import TagStore, BOTH


class TestUnsafeSync(TestCase):
    """ Tests various things related to syncing. Note that it is not possible
        to create pages without cluttering page revision currently, so we have to use
        the testwiki. """

    def setUp(self):
        if not getattr(self.request.cfg, 'is_test_wiki', False):
            py.test.skip('This test needs to be run using the test wiki.')
        self.page = PageEditor(self.request, "FrontPage")

    def testBasicTagThings(self):
        tags = TagStore(self.page)
        self.assert_(not tags.get_all_tags())
        tags.add(remote_wiki="foo", remote_rev=1, current_rev=2, direction=BOTH, normalised_name="FrontPage")
        tags = TagStore(self.page) # reload
        dummy = repr(tags.get_all_tags()) # this should not raise
        self.assert_(tags.get_all_tags()[0].remote_rev == 1)
    
    def tearDown(self):
        tags = TagStore(self.page)
        tags.clear()

