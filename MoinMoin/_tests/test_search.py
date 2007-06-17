# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search Tests

    @copyright: 2005 by Nir Soffer <nirs@freeshell.org>
    @license: GNU GPL, see COPYING for details.
"""

import unittest # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS
from MoinMoin import search


class TestQuotingBug(unittest.TestCase):
    """search: quoting bug tests 
    
    http://moinmoin.wikiwikiweb.de/MoinMoinBugs/SearchOneCharString
    
    This is only a little stupid test for the isQuoted method, because
    testing parsed queries is much more work.
    """

    def setUp(self):
        self.parser = search.QueryParser()

    def testIsQuoted(self):
        """ search: quoting bug - quoted terms """
        for case in ('"yes"', "'yes'"):
            self.assertEqual(self.parser.isQuoted(case), True)

    def testIsNot(self):
        """ search: quoting bug - unquoted terms """
        tests = ('', "'", '"', '""', "''", "'\"", '"no', 'no"', "'no",
                 "no'", '"no\'')
        for case in tests:
            self.assertEqual(self.parser.isQuoted(case), False)

