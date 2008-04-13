# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.macro.EmbedObject Tests

    @copyright: 2008 MoinMoin:ReimarBauer,
                2008 MoinMoin:JohannesBerg

    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin import macro
from MoinMoin.action import AttachFile

from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestEmbedObject:
    """ testing macro Action calling action raw """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPageForEmbedObject'

    def setup_class(self):
        request = self.request
        pagename = self.pagename

        become_trusted(request)
        self.page = create_page(request, pagename, u"Foo")

        AttachFile.getAttachDir(request, pagename)
        test_files = [
            ('test.ogg', u'vorbis'),
            ('test.svg', u'SVG'),
            ('test.mpg', u'MPG'),
            ('test.pdf', u'PDF'),
            ('test.mp3', u'MP3'),
        ]
        for filename, filecontent in test_files:
            AttachFile.add_attachment(request, pagename, filename, filecontent, overwrite=0)

    def teardown_class(self):
        nuke_page(self.request, self.pagename)

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

    def testEmbedObjectMimetype(self):
        """ tests defined mimetyes """
        tests = [
            (u'test.ogg', 'application/ogg'),
            (u'test.svg', 'image/svg+xml'),
            (u'test.mpg', 'video/mpeg'),
            (u'test.mp3', 'audio/mpeg'),
        ]
        for filename, mimetype in tests:
            m = self._make_macro()
            result = m.execute('EmbedObject', filename)
            assert mimetype in result

    def testEmbedObjectDefaultValues(self):
        """ tests default values of macro EmbedObject """
        m = self._make_macro()
        filename = 'test.ogg'
        result = m.execute('EmbedObject', u'%s' % filename)
        assert '<object data="./AutoCreatedMoinMoinTemporaryTestPageForEmbedObject?action=AttachFile&amp;do=get&amp;target=test.ogg"' in result
        assert 'align="middle"' in result
        assert 'value="transparent"' in result

    def testEmbedObjectPercentHeight(self):
        """ tests a unit value for macro EmbedObject """
        m = self._make_macro()
        filename = 'test.ogg'
        height = '50 %' # also tests that space is allowed in there
        result = m.execute('EmbedObject', u'target=%s, height=%s' % (filename, height))
        assert '<object data="./AutoCreatedMoinMoinTemporaryTestPageForEmbedObject?action=AttachFile&amp;do=get&amp;target=test.ogg"' in result
        assert 'height="50%"' in result
        assert 'align="middle"' in result

    def testEmbedObjectFromUrl(self):
        """ tests using a URL for macro EmbedObject """
        m = self._make_macro()
        target = 'http://localhost/%s?action=AttachFile&do=view&target=test.ogg' % self.pagename
        result = m.execute('EmbedObject', u'target=%s, url_mimetype=application/ogg' % target)
        assert '<object data="http://localhost/AutoCreatedMoinMoinTemporaryTestPageForEmbedObject?action=AttachFile&amp;do=view&amp;target=test.ogg" type="application/ogg"' in result

coverage_modules = ['MoinMoin.macro.EmbedObject']
