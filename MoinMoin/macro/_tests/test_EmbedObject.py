# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.macro.EmbedObject Tests

    @copyright: 2008 MoinMoin:ReimarBauer,
                2008 MoinMoin:JohannesBerg

    @license: GNU GPL, see COPYING for details.
"""
import os, py
from MoinMoin import macro
from MoinMoin.action import AttachFile
from MoinMoin.macro import EmbedObject
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor


class TestEmbedObject:
    """ testing macro Action calling action raw """

    def setup_class(self):
        self.pagename = u'AutoCreatedMoinMoinTemporaryTestPageForEmbedObject'
        self.page = PageEditor(self.request, self.pagename)
        AttachFile.getAttachDir(self.request, self.pagename)
        filename = 'test.ogg'
        filecontent = u'vorbis'
        AttachFile.add_attachment(self.request, self.pagename, filename, filecontent, overwrite=0)
        filename = 'test.svg'
        filecontent = u'SVG'
        AttachFile.add_attachment(self.request, self.pagename, filename, filecontent, overwrite=0)
        filename = 'test.mpg'
        filecontent = u'MPG'
        AttachFile.add_attachment(self.request, self.pagename, filename, filecontent, overwrite=0)
        filename = 'test.pdf'
        filecontent = u'PDF'
        AttachFile.add_attachment(self.request, self.pagename, filename, filecontent, overwrite=0)
        filename = 'test.mp3'
        filecontent = u'MP3'
        AttachFile.add_attachment(self.request, self.pagename, filename, filecontent, overwrite=0)
        self.shouldDeleteTestPage = True

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
        """ Test helper """
        from MoinMoin.parser.text import Parser
        from MoinMoin.formatter.text_html import Formatter
        p = Parser("##\n", self.request)
        p.formatter = Formatter(self.request)
        p.formatter.page = self.page
        self.request.formatter = p.formatter
        p.form = self.request.form
        m = macro.Macro(p)
        return m

    def _createTestPage(self, body):
        """ Create temporary page """
        assert body is not None
        self.request.reset()
        self.page.saveText(body, 0)
        
    def testEmbedObjectMimetype(self):
        """ tests defined mimetyes """
        files = ('test.ogg', 'test.svg', 'test.mpg', 'test.mp3')
        mimetype = ('application/ogg', 'image/svg+xml', 'video/mpeg', 'audio/mpeg')
        index = 0
        for filename in files:
            text = '= %s =' % filename
            self._createTestPage(text)
            m = self._make_macro()
            result = m.execute('EmbedObject', u'%s' % filename)
            assert mimetype[index] in result
            index += 1

    def testEmbedObjectDefaultValues(self):
        """ tests default values of macro EmbedObject """
        text = '= Example ='
        self._createTestPage(text)
        m = self._make_macro()
        filename = 'test.ogg'
        result = m.execute('EmbedObject', u'%s' % filename)
        assert '<object data="./AutoCreatedMoinMoinTemporaryTestPageForEmbedObject?action=AttachFile&amp;do=get&amp;target=test.ogg"' in result
        assert 'align="middle"' in result
        assert 'value="transparent"' in result

    def testEmbedObjectPercentHeight(self):
        """ tests a unit value for macro EmbedObject """
        text = '= Example2 ='
        self._createTestPage(text)
        m = self._make_macro()
        filename = 'test.ogg'
        height = '50 %' # also tests that space is allowed in there
        result = m.execute('EmbedObject', u'target=%s, height=%s' % (filename, height))
        assert '<object data="./AutoCreatedMoinMoinTemporaryTestPageForEmbedObject?action=AttachFile&amp;do=get&amp;target=test.ogg"' in result
        assert 'height="50%"' in result
        assert 'align="middle"' in result

    def testEmbedObjectFromUrl(self):
        """ tests using a URL for macro EmbedObject """
        text = '= Example3 ='
        self._createTestPage(text)
        m = self._make_macro()
        target = 'http://localhost/%s?action=AttachFile&do=view&target=test.ogg' % self.pagename
        result = m.execute('EmbedObject', u'target=%s, url_mimetype=application/ogg' % target)
        assert '<object data="http://localhost/AutoCreatedMoinMoinTemporaryTestPageForEmbedObject?action=AttachFile&amp;do=view&amp;target=test.ogg" type="application/ogg"' in result

coverage_modules = ['MoinMoin.macro.EmbedObject']

