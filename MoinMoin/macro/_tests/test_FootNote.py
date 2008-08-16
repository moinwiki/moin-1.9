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
from MoinMoin._tests import become_trusted, create_page, make_macro, nuke_page

class TestFootNote:
    """ testing macro Action calling action raw """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForFootNote'

    def setup_class(self):
        become_trusted(self.request)
        self.page = create_page(self.request, self.pagename, u"Foo!")

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

    def test_enumbering(self):
        """ module_tested: enumbering of Footnotes"""
        m = make_macro(self.request, self.page)
        text = 'a'
        FootNote.execute(m, text)
        text = 'b'
        FootNote.execute(m, text)
        result = FootNote.emit_footnotes(m.request, m.request.formatter)
        assert result.endswith('2</a>)</li></ol></div>')

coverage_modules = ['MoinMoin.macro.FootNote']
