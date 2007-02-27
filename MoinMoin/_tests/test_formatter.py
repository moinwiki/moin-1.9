# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.formatter.* Tests

    @copyright: 2005 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

from unittest import TestCase
import re

from MoinMoin._tests import TestConfig
from MoinMoin.Page import Page
from MoinMoin import wikiutil


class FormatterTestCase(TestCase):
    def testSyntaxReference(self):
        formatters = wikiutil.getPlugins("formatter", self.request.cfg)
        for f_name in formatters:
            #if f_name in ('dom_xml', ):
            #    continue
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

        return self.request.redirectedOutput(page.send_page)

