# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.parser.text_moin_wiki Tests

    TODO: these are actually parser+formatter tests. We should have
    parser only tests here.

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re
from StringIO import StringIO

import py

from MoinMoin.Page import Page
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser
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
        parser = WikiParser(body, request, line_anchors=False)
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
            '|| table ||\n',
            '= heading 1 =\n',
            '== heading 2 ==\n',
            '=== heading 3 ===\n',
            '==== heading 4 ====\n',
            '===== heading 5 =====\n',
            # '<<en>>\n', XXX crashes
            )
        for item in markup:
            text = item + 'Paragraph'
            result = self.parse(text)
            assert re.search(r'<p.*?>\s*Paragraph\s*', result)

    def testStrangeP(self):
        """ parser.wiki: empty line separates paragraphs """
        result = self.parse("""<<BR>> <<BR>>

foo ''bar'' baz.
""")
        assert re.search(r'foo <em>bar</em> baz', result)


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


class TestDateTimeMacro(ParserTestCase):
    """ Test DateTime macro

    If you get failures in these tests, it might be because:
    * libc problems (some are just broken/incorrect)
    * changes in the timezone of a country (e.g. Lithuania seems
      to have changed the tz it is in, see comments below). Our
      timestamps are in UTC, but we use mktime(), which is the inverse
      function of localtime() (NOT of gmtime()), so we have to fix
      our calculation with the tzoffset. Problem: we can't easily find
      out the tzoffset some location had at some time in the past.
      Badly enough, we also don't have an inverse function of gmtime().

    If some of these tests fail and show differences of e.g. 1 hour,
    you might see your timestamps being off by 1 hour in the wiki.
    If you can live with that, this will cause no other problems.
    """

    text = 'AAA %s AAA'
    needle = re.compile(text % r'(.+)')
    _tests = (
        # test                                   expected
        (u'<<DateTime(259200)>>',                '1970-01-04 00:00:00'),
        (u'<<DateTime(2003-03-03T03:03:03)>>',   '2003-03-03 03:03:03'),
        (u'<<DateTime(2000-01-01T00:00:00Z)>>',  '2000-01-01 00:00:00'), # works for Europe/Vilnius
        (u'<<Date(2002-02-02T01:02:03Z)>>',      '2002-02-02'),
        (u'<<DateTime(1970-01-06T00:00:00)>>',   '1970-01-06 00:00:00'), # fails e.g. for Europe/Vilnius
        )

    def testDateTimeMacro(self):
        """ parser.wiki: DateTime macro """
        note = """

    If this fails, it is likely a problem in your python / libc,
    not in moin.  See also: <http://sourceforge.net/tracker/index.php?func=detail&aid=902172&group_id=5470&atid=105470>

    It can also be related to TZ changes a country historically made.
    """

        for test, expected in self._tests:
            html = self.parse(self.text % test)
            result = self.needle.search(html).group(1)
            assert result == expected


class TestTextFormatingTestCase(ParserTestCase):
    """ Test wiki markup """

    text = 'AAA %s AAA'
    needle = re.compile(text % r'(.+)')
    _tests = (
        # test,                     expected
        ('no format',               'no format'),
        ("''em''",                  '<em>em</em>'),
        ("'''bold'''",              '<strong>bold</strong>'),
        ("__underline__",           '<span class="u">underline</span>'),
        ("'''''Mix''' at start''",  '<em><strong>Mix</strong> at start</em>'),
        ("'''''Mix'' at start'''",  '<strong><em>Mix</em> at start</strong>'),
        ("'''Mix at ''end'''''",    '<strong>Mix at <em>end</em></strong>'),
        ("''Mix at '''end'''''",    '<em>Mix at <strong>end</strong></em>'),
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
        py.test.skip("Broken")
        cases = (
            # test, expected
            ("text__text\n", r'<p[^>]*>text<span class="u">text\s*</span></p>'),
            ("text''text\n", r'<p[^>]*>text<em>text\s*</em></p>'),
            ("text'''text\n", r'<p[^>]*>text<strong>text\s*</strong></p>'),
            ("text ''em '''em strong __em strong underline",
             r'text <em>em <strong>em strong <span class="u">em strong underline'
             r'\s*</span></strong></em></p>'),
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
        test = "''a'''ab''b'''\n"
        result = self.parse(test)
        assert re.search(expected, result)


class TestEscapeHTML(ParserTestCase):

    def testEscapeInTT(self):
        """ parser.wiki: escape html markup in `tt` """
        test = 'text `<escape-me>` text\n'
        self._test(test)

    def testEscapeInTT2(self):
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

    def testEscapeInGetTextFormatted(self):
        """ parser.wiki: escape html markup in getText formatted call """
        test = self.request.getText('<escape-me>', wiki=True)
        self._test(test)

    def testEscapeInGetTextFormatedLink(self):
        """ parser.wiki: escape html markup in getText formatted call with link """
        test = self.request.getText('[[<escape-me>]]', wiki=True)
        self._test(test)

    def testEscapeInGetTextUnFormatted(self):
        """ parser.wiki: escape html markup in getText non formatted call """
        test = self.request.getText('<escape-me>', wiki=False)
        self._test(test)

    def _test(self, test):
        expected = r'&lt;escape-me&gt;'
        result = self.parse(test)
        assert re.search(expected, result)


class TestEscapeWikiTableMarkup(ParserTestCase):

    def testEscapeInTT(self):
        """ parser.wiki: escape wiki table markup in `tt` """
        test = 'text `||<tablewidth="80"> Table ||` text\n'
        self.do(test)

    def testEscapeInTT2(self):
        """ parser.wiki: escape wiki table markup in {{{tt}}} """
        test = 'text {{{||<tablewidth="80"> Table ||}}} text\n'
        self.do(test)

    def testEscapeInPre(self):
        """ parser.wiki: escape wiki table  markup in pre """
        test = '''{{{
||<tablewidth="80"> Table ||
}}}
'''
        self.do(test)

    def testEscapeInPreHashbang(self):
        """ parser.wiki: escape wiki table  markup in pre with hashbang """
        test = '''{{{#!
||<tablewidth="80"> Table ||
}}}
'''
        self.do(test)

    def testEscapeInPythonCodeArea(self):
        """ parser.wiki: escape wiki table markup in python code area """
        test = '''{{{#!python
# ||<tablewidth="80"> Table ||
}}}
'''
        self.do(test)

    def do(self, test):
        expected = r'&lt;tablewidth="80"&gt;'
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

    def testVariableRule(self):
        """ parser.wiki: ----- rules with size """

        for size in range(5, 11):
            test = '-' * size
            result = self.parse(test)
            assert re.search(r'<hr class="hr%d".*?>' % (size - 4), result)

    def testLongRule(self):
        """ parser.wiki: ------------ long rule shortened to hr6 """
        test = '-' * 254
        result = self.parse(test)
        assert re.search(r'<hr class="hr6".*?>', result)


class TestBlock(ParserTestCase):
    cases = (
        # test, block start
        ('----\n', '<hr'),
        ('= Heading =\n', '<h1'),
        ('{{{\nPre\n}}}\n', '<pre'),
        ('{{{\n#!python\nPre\n}}}\n', '<div'),
        ('|| Table ||', '<div'),
        (' * unordered list\n', '<ul'),
        (' 1. ordered list\n', '<ol'),
        (' indented text\n', '<ul'),
        )

    def testParagraphBeforeBlock(self):
        """ parser.wiki: paragraph closed before block element """
        text = """AAA
%s
"""
        for test, blockstart in self.cases:
            # We dont test here formatter white space generation
            expected = r'<p.*?>AAA\s*\n*%s' % blockstart
            needle = re.compile(expected, re.MULTILINE)
            result = self.parse(text % test)
            print expected, result
            assert needle.search(result)

    def testEmptyLineBeforeBlock(self):
        """ parser.wiki: empty lines before block element ignored

        Empty lines separate paragraphs, but should be ignored if a block
        element follow.

        Currently an empty paragraph is created, which make no sense but
        no real harm.
        """
        text = """AAA

%s
"""
        for test, blockstart in self.cases:
            expected = r'<p.*?>AAA.*?(<p.*?>\s*)*%s' % blockstart # XXX ignores addtl. <p>
            needle = re.compile(expected, re.MULTILINE)
            result = self.parse(text % test)
            print expected, result
            assert needle.search(result)

    def testUrlAfterBlock(self):
        """ parser.wiki: tests url after block element """
        case = 'some text {{{some block text\n}}} and a URL http://moinmo.in/'

        result = self.parse(case)
        assert result.find('and a URL <a ') > -1

    def testWikiNameAfterBlock(self):
        """ parser.wiki: tests url after block element """
        case = 'some text {{{some block text\n}}} and a WikiName'

        result = self.parse(case)
        assert result.find('and a <a ') > -1

    def testColorizedPythonParserAndNestingPreBrackets(self):
        """ tests nested {{{ }}} for the python colorized parser
        """
        raw = """{{{{
#!python
import re
pattern = re.compile(r'{{{This is some nested text}}}')
}}}}"""
        output = self.parse(raw)
        output = ''.join(output)
        assert "r'{{{This is some nested text}}}'" in output

    def testNestingPreBrackets(self):
        """ tests nested {{{ }}} for the wiki parser
        """
        raw = """{{{{
Example
You can use {{{brackets}}}
}}}}"""
        output = self.parse(raw)
        output = ''.join(output)
        print output
        assert 'You can use {{{brackets}}}' in output

    def testTextBeforeNestingPreBrackets(self):
        """ tests text before nested {{{ }}} for the wiki parser
        """
        raw = """Example
        {{{{
You can use {{{brackets}}}
}}}}"""
        output = self.parse(raw)
        output = ''.join(output)
        assert 'Example <ul><li style="list-style-type:none"><pre>You can use {{{brackets}}}</pre>' in output

    def testManyNestingPreBrackets(self):
        """ tests two nestings  ({{{ }}} and {{{ }}}) in one line for the wiki parser
        """
        raw = """{{{{
Test {{{brackets}}} and test {{{brackets}}}
}}}}"""
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
        ('SomeNonExistentPage', '<a class="nonexistent" href="./SomeNonExistentPage">SomeNonExistentPage</a>'),
        ('SomeNonExistentPage#anchor', '<a class="nonexistent" href="./SomeNonExistentPage#anchor">SomeNonExistentPage#anchor</a>'),
        ('[[something]]', '<a class="nonexistent" href="./something">something</a>'),
        ('[[some thing]]', '<a class="nonexistent" href="./some%20thing">some thing</a>'),
        ('[[something|some text]]', '<a class="nonexistent" href="./something">some text</a>'),
        ('[[../something]]', '<a class="nonexistent" href="./something">../something</a>'),
        ('[[/something]]', '<a class="nonexistent" href="./%s/something">/something</a>' % PAGENAME),
        ('[[something#anchor]]', '<a class="nonexistent" href="./something#anchor">something#anchor</a>'),
        ('MoinMoin:something', '<a class="interwiki" href="http://moinmo.in/something" title="MoinMoin">something</a>'),
        ('[[MoinMoin:something|some text]]', '<a class="interwiki" href="http://moinmo.in/something" title="MoinMoin">some text</a>'),
        ('[[MoinMoin:with space]]', '<a class="interwiki" href="http://moinmo.in/with%20space" title="MoinMoin">with space</a>'),
        ('[[MoinMoin:with space|some text]]', '<a class="interwiki" href="http://moinmo.in/with%20space" title="MoinMoin">some text</a>'),
        # no interwiki:
        ('[[ABC:n]]', '<a class="nonexistent" href="./ABC%3An">ABC:n</a>'), # finnish/swedish abbreviations / possessive
        ('ABC:n', 'ABC:n'), # finnish/swedish abbreviations / possessive
        ('lowercase:nointerwiki', 'lowercase:nointerwiki'),
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


class TestTransclusionMarkup(ParserTestCase):
    """ Test wiki markup """

    text = 'AAA %s AAA'
    needle = re.compile(text % r'(.+)')
    _tests = [
        # test,           expected
        ('{{http://moinmo.in/wiki/common/moinmoin.png}}', '<img alt="http://moinmo.in/wiki/common/moinmoin.png" class="external_image" src="http://moinmo.in/wiki/common/moinmoin.png" title="http://moinmo.in/wiki/common/moinmoin.png" />'),
        ('{{http://moinmo.in/wiki/common/moinmoin.png|moin logo}}', '<img alt="moin logo" class="external_image" src="http://moinmo.in/wiki/common/moinmoin.png" title="moin logo" />'),
        ]

    def testTransclusionFormating(self):
        """ parser.wiki: transclusion formating """
        for test, expected in self._tests:
            html = self.parse(self.text % test)
            result = self.needle.search(html).group(1)
            assert result == expected

class TestMacrosInOneLine(ParserTestCase):
    """ Test macro formatting """
    text = 'AAA %s AAA'
    needle = re.compile(text % r'(.+)')
    _tests = (
        # test                              expected
        (u'<<Verbatim(A)>><<Verbatim(a)>>', 'Aa'),
        (u'<<Verbatim(A)>> <<Verbatim(a)>>', 'A a'),
        )

    def testMultipleMacrosInOneLine(self):
        """ parser.wiki: multiple macros in one line and no linebreak """
        for test, expected in self._tests:
            html = self.parse(self.text % test)
            result = self.needle.search(html).group(1)
            assert result == expected


coverage_modules = ['MoinMoin.parser.text_moin_wiki']

