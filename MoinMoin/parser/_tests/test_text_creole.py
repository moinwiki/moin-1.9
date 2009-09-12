# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.parser.text_creole Tests

    TODO: these are actually parser+formatter tests. We should have
    parser only tests here.

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re
from StringIO import StringIO

import py

from MoinMoin.Page import Page
from MoinMoin.parser.text_creole import Parser as CreoleParser
from MoinMoin.formatter.text_html import Formatter as HtmlFormatter

PAGENAME = u'ThisPageDoesNotExistsAndWillNeverBeReally'

class ParserTestCase(object):
    """ Helper class that provide a parsing method """

    def parse(self, body):
        """Parse body and return html

        Create a page with body, then parse it and format using html formatter
        """
        request = self.request
        assert body is not None
        request.reset()
        page = Page(request, PAGENAME)
        page.hilite_re = None
        page.set_raw_body(body)
        formatter = HtmlFormatter(request)
        formatter.setPage(page)
        page.formatter = formatter
        request.formatter = formatter
        request.page = page
        parser = CreoleParser(body, request, line_anchors=False)
        formatter.startContent('') # needed for _include_stack init
        output = request.redirectedOutput(parser.format, formatter)
        formatter.endContent('')
        return output


class TestParagraphs(ParserTestCase):
    """ Test paragraphs creating

    All tests ignoring white space in output.
    We do not test for </p> as it is not there currently.
    """

    def testFirstParagraph(self):
        """ parser.wiki: first paragraph should be in <p> """
        result = self.parse('First')
        assert re.search(r'<p.*?>\s*First\s*', result)

    def testEmptyLineBetweenParagraphs(self):
        """ parser.wiki: empty line separates paragraphs """
        result = self.parse('First\n\nSecond')
        assert re.search(r'<p.*?>\s*Second\s*', result)

    def testParagraphAfterBlockMarkup(self):
        """ parser.wiki: create paragraph after block markup """

        markup = (
            '----\n',
            '| table |\n',
            '= heading 1 =\n',
            '== heading 2 ==\n',
            '=== heading 3 ===\n',
            '==== heading 4 ====\n',
            '===== heading 5 =====\n',
            )
        for item in markup:
            text = item + 'Paragraph'
            result = self.parse(text)
            assert re.search(r'<p.*?>\s*Paragraph\s*', result)


class TestHeadings(ParserTestCase):
    """ Test various heading problems """

    def testIgnoreWhiteSpaceAroundHeadingText(self):
        """ parser.wiki: ignore white space around heading text

        See bug: TableOfContentsBreakOnExtraSpaces.

        Does not test mapping of '=' to h number, or valid html markup.
        """
        tests = (
            '=  head =\n', # leading
            '= head  =\n', # trailing
            '=  head  =\n' # both
                 )
        expected = self.parse('= head =')
        for test in tests:
            result = self.parse(test)
            assert result == expected


class TestTOC(ParserTestCase):

    def testHeadingWithWhiteSpace(self):
        """ parser.wiki: TOC links to headings with white space

        See bug: TableOfContentsBreakOnExtraSpaces.

        Does not test TOC or heading formating, just verify that spaces
        around heading text does not matter.
        """
        standard = """
<<TableOfContents>>
= heading =
Text
"""
        withWhitespace = """
<<TableOfContents>>
=   heading   =
Text
"""
        expected = self.parse(standard)
        result = self.parse(withWhitespace)
        assert  result == expected


class TestTextFormatingTestCase(ParserTestCase):
    """ Test wiki markup """

    text = 'AAA %s AAA'
    needle = re.compile(text % r'(.+)')
    _tests = (
        # test,                     expected
        ('no format',               'no format'),
        ("//em//",                  '<em>em</em>'),
        ("**bold**",              '<strong>bold</strong>'),
        ("//**Mix** at start//",  '<em><strong>Mix</strong> at start</em>'),
        ("**//Mix// at start**",  '<strong><em>Mix</em> at start</strong>'),
        ("**Mix at //end//**",    '<strong>Mix at <em>end</em></strong>'),
        ("//Mix at **end**//",    '<em>Mix at <strong>end</strong></em>'),
        )

    def testTextFormating(self):
        """ parser.wiki: text formating """
        for test, expected in self._tests:
            html = self.parse(self.text % test)
            result = self.needle.search(html).group(1)
            assert result == expected


class TestCloseInlineTestCase(ParserTestCase):

    def testCloseOneInline(self):
        """ parser.wiki: close open inline tag when block close """
        cases = (
            # test, expected
            ("text**text\n", r"<p>text<strong>text\s*</strong></p>"),
            ("text//text\n", r"<p>text<em>text\s*</em></p>"),
            ("text //em **em strong", r"text <em>em <strong>em strong"),
        )
        for test, expected in cases:
            result = self.parse(test)
            assert re.search(expected, result)


class TestInlineCrossing(ParserTestCase):
    """
    This test case fail with current parser/formatter and should be fixed in 2.0
    """

    def disabled_testInlineCrossing(self):
        """ parser.wiki: prevent inline crossing <a><b></a></b> """

        expected = (r"<p><em>a<strong>ab</strong></em><strong>b</strong>\s*</p>")
        test = "//a**ab//b**\n"
        result = self.parse(test)
        assert re.search(expected, result)


class TestEscapeHTML(ParserTestCase):

    def testEscapeInTT(self):
        """ parser.wiki: escape html markup in {{{tt}}} """
        test = 'text {{{<escape-me>}}} text\n'
        self._test(test)

    def testEscapeInPre(self):
        """ parser.wiki: escape html markup in pre """
        test = '''{{{
<escape-me>
}}}
'''
        self._test(test)

    def testEscapeInPreHashbang(self):
        """ parser.wiki: escape html markup in pre with hashbang """
        test = '''{{{#!
<escape-me>
}}}
'''
        self._test(test)

    def testEscapeInPythonCodeArea(self):
        """ parser.wiki: escape html markup in python code area """
        test = '''{{{#!python
#<escape-me>
}}}
'''
        self._test(test)

    def testEscapeInGetTextMacro(self):
        """ parser.wiki: escape html markup in GetText macro """
        test = u"text <<GetText(<escape-me>)>> text"
        self._test(test)

# Getting double escaping
#
#    def testEscapeInGetTextFormatted(self):
#        """ parser.wiki: escape html markup in getText formatted call """
#        test = self.request.getText('<escape-me>', wiki=True)
#        self._test(test)
#
#    def testEscapeInGetTextFormatedLink(self):
#        """ parser.wiki: escape html markup in getText formatted call with link """
#        test = self.request.getText('[[<escape-me>]]', wiki=True)
#        self._test(test)

    def testEscapeInGetTextUnFormatted(self):
        """ parser.wiki: escape html markup in getText non formatted call """
        test = self.request.getText('<escape-me>', wiki=False)
        self._test(test)

    def _test(self, test):
        expected = r'&lt;escape-me&gt;'
        result = self.parse(test)
        assert re.search(expected, result)



class TestRule(ParserTestCase):
    """ Test rules markup """

    def testNotRule(self):
        """ parser.wiki: --- is no rule """
        result = self.parse('---')
        expected = '---' # inside <p>
        assert expected in result

    def testStandardRule(self):
        """ parser.wiki: ---- is standard rule """
        result = self.parse('----')
        assert re.search(r'<hr.*?>', result)

    def testLongRule(self):
        """ parser.wiki: ----- is no rule """
        test = '-----'
        result = self.parse(test)
        assert re.search(r'-----', result)


class TestBlock(ParserTestCase):
    cases = (
        # test, block start
        ('----\n', '<hr'),
        ('= Heading =\n', '<h1'),
        ('{{{\nPre\n}}}\n', '<pre'),
        ('{{{\n#!python\nPre\n}}}\n', '<div'),
        ('| Table |\n', '<div'),
        (' * unordered list\n', '<ul'),
        (' # ordered list\n', '<ol'),
        )

    def testParagraphBeforeBlock(self):
        """ parser.wiki: paragraph closed before block element """
        text = """AAA
%s
"""
        for test, blockstart in self.cases:
            # We dont test here formatter white space generation
            expected = r'<p.*?>AAA\s*</p>\s*%s' % blockstart
            needle = re.compile(expected, re.MULTILINE)
            result = self.parse(text % test)
            assert needle.search(result)

    def testUrlAfterBlock(self):
        """ parser.wiki: tests url after block element """
        case = 'some text {{{some block text\n}}} and a URL http://moinmo.in/'

        result = self.parse(case)
        assert result.find('and a URL <a ') > -1

    def testColorizedPythonParserAndNestingPreBrackets(self):
        """ tests nested {{{ }}} for the python colorized parser
        """

        raw = """{{{
#!python
import re
pattern = re.compile(r'{{{This is some nested text}}}')
}}}"""
        output = self.parse(raw)
        output = ''.join(output)
        assert "{{{This is some nested text}}}" in output

    def testNestingPreBracketsWithLinebreak(self):
        """ tests nested {{{ }}} for the wiki parser
        """

        raw = """{{{
Example
You can use {{{brackets}}}
}}}"""
        output = self.parse(raw)
        output = ''.join(output)
        print output
        assert 'You can use {{{brackets}}}' in output

    def testTextBeforeNestingPreBrackets(self):
        """ tests text before nested {{{ }}} for the wiki parser
        """
        raw = """Example
{{{
You can use {{{brackets}}}
}}}"""
        output = self.parse(raw)
        output = ''.join(output)
        assert 'Example</p><pre>You can use {{{brackets}}}</pre>' in output

    def testManyNestingPreBrackets(self):
        """ tests two nestings  ({{{ }}} and {{{ }}}) in one line for the wiki parser
        """

        raw = """{{{
Test {{{brackets}}} and test {{{brackets}}}
}}}"""
        output = self.parse(raw)
        output = ''.join(output)
        expected = '<pre>Test {{{brackets}}} and test {{{brackets}}}'
        assert expected in output

    def testMultipleShortPreSections(self):
        """
        tests two single {{{ }}} in one line
        """
        raw = 'def {{{ghi}}} jkl {{{mno}}}'
        output = ''.join(self.parse(raw))
        expected = 'def <tt>ghi</tt> jkl <tt>mno</tt>'
        assert expected in output

class TestLinkingMarkup(ParserTestCase):
    """ Test wiki link markup """

    text = 'AAA %s AAA'
    needle = re.compile(text % r'(.+)')
    _tests = [
        # test,           expected
        ('[[SomeNonExistentPage]]', '<a class="nonexistent" href="/SomeNonExistentPage">SomeNonExistentPage</a>'),
        ('[[SomeNonExistentPage#anchor]]', '<a class="nonexistent" href="/SomeNonExistentPage#anchor">SomeNonExistentPage#anchor</a>'),
        ('[[something]]', '<a class="nonexistent" href="/something">something</a>'),
        ('[[some thing]]', '<a class="nonexistent" href="/some%20thing">some thing</a>'),
        ('[[something|some text]]', '<a class="nonexistent" href="/something">some text</a>'),
        ('[[../something]]', '<a class="nonexistent" href="/something">../something</a>'),
        ('[[/something]]', '<a class="nonexistent" href="/%s/something">/something</a>' % PAGENAME),
        ('[[something#anchor]]', '<a class="nonexistent" href="/something#anchor">something#anchor</a>'),
        ('[[MoinMoin:something]]', '<a class="interwiki" href="http://moinmo.in/something" title="MoinMoin">something</a>'),
        ('[[MoinMoin:something|some text]]', '<a class="interwiki" href="http://moinmo.in/something" title="MoinMoin">some text</a>'),
        ('[[MoinMoin:with space]]', '<a class="interwiki" href="http://moinmo.in/with%20space" title="MoinMoin">with space</a>'),
        ('[[MoinMoin:with space|some text]]', '<a class="interwiki" href="http://moinmo.in/with%20space" title="MoinMoin">some text</a>'),
        ('[[http://google.com/|google]]', '<a class="http" href="http://google.com/">google</a>'),
        ]

    def testLinkFormating(self):
        """ parser.wiki: link formating """
        for test, expected in self._tests:
            html = self.parse(self.text % test)
            result = self.needle.search(html).group(1)
            assert result == expected

    def testLinkAttachment(self):
        html = self.parse("[[attachment:some file.txt]]")
        assert '<a ' in html
        assert 'href="' in html
        assert 'class="attachment nonexistent"' in html
        assert 'action=AttachFile' in html
        assert 'some+file.txt' in html

    def testLinkAttachmentImage(self):
        html = self.parse("[[attachment:some file.png]]")
        assert '<a ' in html # must create a link
        assert 'href="' in html
        assert 'class="attachment nonexistent"' in html
        assert 'action=AttachFile' in html
        assert 'some+file.png' in html

    def testAnchor(self):
        html = self.parse("{{#anchor}}")
        assert 'id="anchor"' in html

coverage_modules = ['MoinMoin.parser.text_creole']

