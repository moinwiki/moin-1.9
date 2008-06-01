# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.macro.Action Tests

    @copyright: 2007 MoinMoin:ReimarBauer

    @license: GNU GPL, see COPYING for details.
"""
import os
from MoinMoin import macro
from MoinMoin.macro import Action
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor

from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestAction:
    """ testing macro Action calling action raw """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForAction'

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

    def testActionCallingRaw(self):
        """ module_tested: executes raw by macro Action on existing page"""
        request = self.request
        become_trusted(request)

        self.page = create_page(request, self.pagename, u'= title1 =\n||A||B||\n')
        m = self._make_macro()
        result = Action.macro_Action(m, 'raw')
        nuke_page(request, self.pagename)

        expected = '<a href="./AutoCreatedMoinMoinTemporaryTestPageForAction?action=raw">raw</a>'
        assert result == expected


coverage_modules = ['MoinMoin.macro.Action']

