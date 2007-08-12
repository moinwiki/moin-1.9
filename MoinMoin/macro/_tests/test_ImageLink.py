# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.macro ImageLink tested

    @copyright: 2007 MoinMoin:ReimarBauer

    @license: GNU GPL, see COPYING for details.
"""
import os
from MoinMoin import macro
from MoinMoin.logfile import eventlog
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.parser.text_moin_wiki import Parser

class TestHits:
    """Hits: testing Hits macro """

    def setup_class(self):
        self.pagename = u'AutoCreatedMoinMoinTemporaryTestPageForImageLink'
        self.page = PageEditor(self.request, self.pagename)
        self.shouldDeleteTestPage = False

    def teardown_class(self):
        if self.shouldDeleteTestPage:
            import shutil
            page = Page(self.request, self.pagename)
            fpath = page.getPagePath(use_underlay=0, check_create=0)
            shutil.rmtree(fpath, True)

            fpath = self.request.rootpage.getPagePath('event-log', isfile=1)
            if os.path.exists(fpath):
                os.remove(fpath)

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

    def _test_macro(self, name, args):
        m = self._make_macro()
        return m.execute(name, args)

    def _createTestPage(self, body):
        """ Create temporary page """
        assert body is not None
        self.request.reset()
        self.page.saveText(body, 0)

    def testImageLinkNoArg(self):
        """ macro ImageLink test: 'no args for ImageLink (ImageLink is executed on FrontPage) """
        #self._createTestPage('This is an example to test a macro')
        result = self._test_macro('ImageLink', '')
        expected = '<div class="message">Not enough arguments to ImageLink macro! e.g. <<ImageLink(example.png, WikiName, width=200)>>.</div>'
        assert result == expected

    def testImageLinkTwoParamsNoKeyword(self):
        """ macro ImageLink test: <<ImageLink(http://static.wikiwikiweb.de/logos/moindude.png, FrontPage)>> """
        self.shouldDeleteTestPage = False

        result = self._test_macro('ImageLink', 'http://static.wikiwikiweb.de/logos/moindude.png, FrontPage')
        expected = '<a href="./FrontPage"><img alt="FrontPage" src="http://static.wikiwikiweb.de/logos/moindude.png" title="FrontPage" /></a>'
        assert result == expected

    def testImageLinkTwoParamsOneKeyword(self):
        """ macro ImageLink test: <<ImageLink(http://static.wikiwikiweb.de/logos/moindude.png, alt=The old dude, FrontPage)>>
        order of keywords to parameter list is independent
        """
        self.shouldDeleteTestPage = True

        result = self._test_macro('ImageLink', 'http://static.wikiwikiweb.de/logos/moindude.png, alt=The old dude, FrontPage')
        expected = '<a href="./FrontPage"><img alt="The old dude" src="http://static.wikiwikiweb.de/logos/moindude.png" title="The old dude" /></a>'
        assert result == expected


coverage_modules = ['MoinMoin.macro.ImageLink']

