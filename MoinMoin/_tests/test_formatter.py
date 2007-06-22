# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.formatter.* Tests

    @copyright: 2005 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import py

import re

from MoinMoin.Page import Page
from MoinMoin import wikiutil


class TestFormatter:
    def testSyntaxReferenceDomXml(self):
        py.test.skip("dom_xml formatter is known to be broken")
        f_name = 'dom_xml'
        try:
            formatter = wikiutil.importPlugin(self.request.cfg, "formatter", f_name, "Formatter")
        except wikiutil.PluginAttributeError:
            pass
        else:
            print "Formatting using %r" % formatter
            self.formatPage("SyntaxReference", formatter)
            print "Done."

    def testSyntaxReferenceDocBook(self):
        py.test.skip("breaks with an attribute error, it should be checked whether the formatter on the DB branch is broken as well")
        try:
            from xml.dom import getDOMImplementation
            dom = getDOMImplementation("4DOM")
        except ImportError:
            # if we don't have 4suite installed, the docbook formatter would just raise an exception
            py.test.skip("not testing docbook formatter because no 4suite installed")
        else:
            f_name = 'text_docbook'
            try:
                formatter = wikiutil.importPlugin(self.request.cfg, "formatter", f_name, "Formatter")
            except wikiutil.PluginAttributeError:
                pass
            else:
                print "Formatting using %r" % formatter
                self.formatPage("SyntaxReference", formatter)
                print "Done."

    def testSyntaxReferenceOthers(self):
        formatters = wikiutil.getPlugins("formatter", self.request.cfg)

        # we have separate tests for those:
        formatters.remove('text_docbook')
        formatters.remove('dom_xml')

        for f_name in formatters:
            try:
                formatter = wikiutil.importPlugin(self.request.cfg, "formatter", f_name, "Formatter")
            except wikiutil.PluginAttributeError:
                pass
            else:
                print "Formatting using %r" % formatter
                self.formatPage("SyntaxReference", formatter)
                print "Done."

    def formatPage(self, pagename, formatter):
        """Parse a page. Should not raise an exception if the API of the
        formatter is correct.
        """

        self.request.reset()
        page = Page(self.request, pagename, formatter=formatter)
        self.request.formatter = page.formatter = formatter(self.request)
        #page.formatter.setPage(page)
        #page.hilite_re = None

        return self.request.redirectedOutput(page.send_page, content_only=1)

