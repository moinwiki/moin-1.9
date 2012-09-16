# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.formatter.* Tests

    @copyright: 2005 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin.Page import Page
from MoinMoin import wikiutil


class TestFormatter:
    def testSyntaxReferenceDomXml(self):
        py.test.skip("domxml <p> generation is broken")
        f_name = 'dom_xml'
        try:
            formatter = wikiutil.importPlugin(self.request.cfg, "formatter", f_name, "Formatter")
        except wikiutil.PluginAttributeError:
            pass
        else:
            print "Formatting using %r" % formatter
            self.formatPage("HelpOnMoinWikiSyntax", formatter)
            print "Done."

    def testSyntaxReferenceDocBook(self):
        py.test.skip("docbook is broken")
        f_name = 'text_docbook'
        try:
            formatter = wikiutil.importPlugin(self.request.cfg, "formatter", f_name, "Formatter")
        except wikiutil.PluginAttributeError:
            pass
        else:
            print "Formatting using %r" % formatter
            self.formatPage("HelpOnMoinWikiSyntax", formatter)
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
                self.formatPage("HelpOnMoinWikiSyntax", formatter)
                print "Done."

    def formatPage(self, pagename, formatter):
        """Parse a page. Should not raise an exception if the API of the
        formatter is correct.
        """

        self.request.reset()
        page = Page(self.request, pagename, formatter=formatter)
        self.request.formatter = page.formatter = formatter(self.request)
        self.request.page = page
        #page.formatter.setPage(page)
        #page.hilite_re = None

        return self.request.redirectedOutput(page.send_page, content_only=1)


class TestIdIdempotency:
    def test_sanitize_to_id_idempotent(self):
        def _verify(formatter, id):
            origid = formatter.sanitize_to_id(id)
            id = origid
            for i in xrange(3):
                id = formatter.sanitize_to_id(id)
                assert id == origid

        formatters = wikiutil.getPlugins("formatter", self.request.cfg)

        testids = [
            r"tho/zeequeen&angu\za",
            r"quuirahz\iphohsaij,i",
            r"ashuifa+it[ohchieque",
            r"ohyie-lakoo`duaghaib",
            r"eixaepumuqu[ie\ba|eh",
            r"theegieque;zahmeitie",
            r"pahcooje&rahkeiz$oez",
            r"ohjeeng*iequao%fai?p",
            r"ahfoodahmepooquepee;",
            r"ubed_aex;ohwebeixah%",
            r"eitiekicaejuelae=g^u",
            r"",
            r'  ',
            r'--123',
            r'__$$',
            r'@@',
            u'\xf6\xf6llasdf\xe4',
        ]

        for f_name in formatters:
            try:
                formatter = wikiutil.importPlugin(self.request.cfg, "formatter",
                                                  f_name, "Formatter")
                f = formatter(self.request)
                for id in testids:
                    yield _verify, f, id
            except wikiutil.PluginAttributeError:
                pass

coverage_modules = ['MoinMoin.formatter',
                    'MoinMoin.formatter.text_html',
                    'MoinMoin.formatter.text_gedit',
                    'MoinMoin.formatter.text_xml',
                    'MoinMoin.formatter.text_docbook',
                    'MoinMoin.formatter.text_plain',
                    'MoinMoin.formatter.dom_xml',
                    'MoinMoin.formatter.text_python',
                    'MoinMoin.formatter.pagelinks',
                    'MoinMoin.formtter.groups',
                   ]

