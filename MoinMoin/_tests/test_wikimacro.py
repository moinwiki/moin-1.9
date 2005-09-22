# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikimacro Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest, os

from MoinMoin import wikimacro, wikiutil
from MoinMoin.parser.plain import Parser
from MoinMoin.formatter.text_html import Formatter


class MacroTestCase(unittest.TestCase):
    def testTrivialMacro(self):
        """wikimacro: trivial macro works"""
        m = self._make_macro()
        expected = m.formatter.linebreak(0)
        result = m.execute("BR", "")
        self.assertEqual(result, expected,
            'Expected "%(expected)s" but got "%(result)s"' % locals())        

    def _make_macro(self):
        """Test helper"""
        p = Parser("##\n", self.request)
        p.formatter = Formatter(self.request)
        self.request.formatter = p.formatter
        p.form = self.request.form
        m = wikimacro.Macro(p)
        return m
