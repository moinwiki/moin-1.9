# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import macro
from MoinMoin.parser.text import Parser
from MoinMoin.formatter.text_html import Formatter
from MoinMoin._tests import become_trusted, create_page, make_macro, nuke_page

class TestMacro:
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForTestMacro'

    def setup_class(self):
        request = self.request
        become_trusted(request)
        self.page = create_page(request, self.pagename, u"Foo!")

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def testTrivialMacro(self):
        """macro: trivial macro works"""
        m = make_macro(self.request, self.page)
        expected = m.formatter.linebreak(0)
        result = m.execute("BR", "")
        assert result == expected

coverage_modules = ['MoinMoin.macro']

