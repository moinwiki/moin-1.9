# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.Page Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS
from MoinMoin import Page

class TestExists(unittest.TestCase):
    """Page: testing wiki page"""

    def testExists(self):
        """ Page: page.exists() finds existing pages only """
        tests = (
            # Page name,                            expected
            ('FrontPage',                           1),
            ('OnlyAnIdiotWouldCreateSuchaPage',     0),
            )
        for name, expected in tests:
            pg = Page.Page(self.request, name)
            self.assertEqual(pg.exists(), expected,
                             '%s should%s exist' % (name, (' not', '')[expected]))
