# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.macro.FootNote Tests

    @copyright: 2008 MoinMoin:ReimarBauer

    @license: GNU GPL, see COPYING for details.
"""
import os
from MoinMoin import macro
from MoinMoin.macro import FootNote
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor

from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestFootNote:
    """ testing macro Action calling action raw """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForFootNote'

    def setup_class(self):
        become_trusted(self.request)
        self.page = create_page(self.request, self.pagename, u"Foo!")

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def _make_macro(self):
        """Test helper"""
        from MoinMoin.parser.text import Parser
        from MoinMoin.formatter.text_html import Formatter
        p = Parser("##\n", self.request)
        p.formatter = Formatter(self.request)
        p.formatter.page = self.page
        self.request.formatter = p.formatter
        p.form = self.request.form
        m = macro.Macro(p)
        return m

    def test_enumbering(self):
        """ module_tested: enumbering of Footnotes"""
        m = self._make_macro()
        text = 'a'
        FootNote.execute(m, text)
        text = 'b'
        FootNote.execute(m, text)
        result = FootNote.emit_footnotes(m.request, m.request.formatter)

        assert result.endswith('2</a>)</li></ol></div>')


coverage_modules = ['MoinMoin.macro.FootNote']
