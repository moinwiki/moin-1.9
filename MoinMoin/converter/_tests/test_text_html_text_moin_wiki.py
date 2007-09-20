# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.text_html_text_moin_wiki Tests

    @copyright: 2005 by Bastian Blank,
                2005,2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py
#py.test.skip("Many broken tests, much broken code, broken, broken, broken.")

from cStringIO import StringIO
from MoinMoin.converter import text_html_text_moin_wiki as converter
from MoinMoin.parser.text_moin_wiki import Parser
from MoinMoin.formatter.text_gedit import Formatter
from MoinMoin.request import Clock
from MoinMoin.error import ConvertError

convert = converter.convert
error = ConvertError


class TestBase(object):

    def setup_method(self, method):
        self.cfg = self.TestConfig(bang_meta=True)

    def teardown_method(self, method):
        del self.cfg

    def do_convert_real(self, func_args, successful=True):
        try:
            ret = convert(*func_args)
        except error, e:
            if successful:
                py.test.fail("fails with parse error: %s" % e)
            else:
                return
        if successful:
            return ret
        else:
            py.test.fail("doesn't fail with parse error")


class MinimalPage(object):
    def __init__(self):
        self.hilite_re = None
        self.page_name = "testpage"


class MinimalRequest(object):
    # TODO: do we really need this class? no other test uses a request replacement.

    def __init__(self, request):
        self.request = request
        self.clock = Clock()

        # This is broken - tests that need correct content_lang will fail
        self.content_lang = None
        self.current_lang = None

        self.form = {}
        self._page_headings = {}
        self.result = []

    def getText(self, text, formatted=True):
        return text

    def write(self, text):
        self.result.append(text)

    def __getattr__(self, name):
        return getattr(self.request, name)


class TestConvertBlockRepeatable(TestBase):
    def do(self, text, output):
        text = text.lstrip('\n')
        output = output.strip('\n')
        request = MinimalRequest(self.request)
        page = MinimalPage()
        formatter = Formatter(request)
        formatter.setPage(page)
        Parser(text, request).format(formatter)
        repeat = ''.join(request.result).strip('\n')
        #assert repeat == output
        out = self.do_convert_real([request, page.page_name, repeat])

        assert text == out

    def testComment01(self):
        test = ur"""
##test
"""
        output = u"""<pre class="comment">\n##test</pre>"""
        self.do(test, output)

    def testComment02(self):
        test = ur"""
##test
##test
"""
        output = u"""
<pre class="comment">\n##test</pre>
<pre class="comment">\n##test</pre>
"""
        self.do(test, output)

    def testHeading01(self):
        py.test.skip('broken test')
        test = ur"""
= test1 =

"""
        output = ur"""
<h2>test1</h2>
"""
        self.do(test, output)

    def testHeading02(self):
        py.test.skip('broken test')
        test = ur"""
= test1 =

== test2 ==

"""
        output = ur"""
<h2>test1</h2>
<h3>test2</h3>
"""
        self.do(test, output)

    def testListSuccess01(self):
        test = ur"""
 * test

"""
        output = ur"""
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess02(self):
        test = ur"""
 1. test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess03(self):
        test = ur"""
 test:: test

"""
        output = ur"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess04(self):
        test = ur"""
 * test
 * test

"""
        output = ur"""
<ul>
<li><p>test </p>
</li>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess05(self):
        test = ur"""
 1. test
 1. test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
</li>
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess06(self):
        test = ur"""
 test:: test
 test:: test

"""
        output = ur"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess07(self):
        test = ur"""
 * test

 * test

"""
        output = ur"""
<ul>
<li><p>test </p>
</li>
</ul>
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess08(self):
        test = ur"""
 1. test

 1. test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess09(self):
        py.test.skip('broken test')
        test = ur"""
 test:: test

 test:: test

"""
        output = ur"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess10(self):
        py.test.skip('broken test')
        test = ur"""
 * test
  * test

"""
        output = ur"""
<ul>
<li><p>test </p>
<ul>
<li><p>test </p>
</li>
</ul>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess11(self):
        py.test.skip('broken test')
        test = ur"""
 1. test
  1. test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
<ol type="1">
<li><p>test </p>
</li>
</ol>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess12(self):
        py.test.skip('broken test')
        test = ur"""
 test:: test
  test:: test

"""
        output = ur"""
<dl>
<dt>test</dt>
<dd><p>test </p>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess13(self):
        test = ur"""
 * test
  * test
 * test

"""
        output = ur"""
<ul>
<li><p>test </p>
<ul>
<li><p>test </p>
</li>
</ul>
</li>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess14(self):
        test = ur"""
 1. test
  1. test
 1. test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
<ol type="1">
<li><p>test </p>
</li>
</ol>
</li>
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess15(self):
        test = ur"""
 test:: test
  test:: test
 test:: test

"""
        output = ur"""
<dl>
<dt>test</dt>
<dd><p>test </p>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
</dd>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess16(self):
        py.test.skip('broken test')
        test = ur"""
 * test

 1. test

"""
        output = ur"""
<ul>
<li><p>test </p>
</li>
</ul>
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess17(self):
        py.test.skip('broken test')
        test = ur"""
 * test

 test:: test

"""
        output = ur"""
<ul>
<li><p>test </p>
</li>
</ul>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess18(self):
        py.test.skip('broken test')
        test = ur"""
 1. test

 * test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess19(self):
        py.test.skip('broken test')
        test = ur"""
 1. test

 test:: test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
</li>
</ol>
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
"""
        self.do(test, output)

    def testListSuccess20(self):
        py.test.skip('broken test')
        test = ur"""
 test:: test

 * test

"""
        output = ur"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
<ul>
<li><p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess21(self):
        py.test.skip('broken test')
        test = ur"""
 test:: test

 1. test

"""
        output = ur"""
<dl>
<dt>test</dt>
<dd><p>test </p>
</dd>
</dl>
<ol type="1">
<li><p>test </p>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess23(self):
        py.test.skip('broken test')
        test = ur"""
 1. test
  * test

"""
        output = ur"""
<ol type="1">
<li><p>test </p>
<ul>
<li><p>test </p>
</li>
</ul>
</li>
</ol>
"""
        self.do(test, output)

    def testListSuccess26(self):
        py.test.skip('broken test')
        test = ur"""
 * test

test

"""
        output = ur"""
<ul>
<li><p>test </p>
</li>
</ul>
<p>test </p>
"""
        self.do(test, output)

    def testListSuccess28(self):
        py.test.skip('broken test')
        test = ur"""
 * test

 test

"""
        output = ur"""
<ul>
<li><p>test </p>
<p>test </p>
</li>
</ul>
"""
        self.do(test, output)

    def testListSuccess29(self):
        py.test.skip('broken test')
        test = ur"""
 * test
  * test
 test
"""
        output = ur"""
"""
        self.do(test, output)

    def testListSuccess30(self):
        py.test.skip('broken test')
        test = ur"""
 * test
  * test
  test
"""
        output = ur"""
"""
        self.do(test, output)

    def testParagraph1(self):
        py.test.skip('broken test')
        test = ur"""
test

"""
        output = ur"""
<p>test </p>
"""
        self.do(test, output)

    def testParagraph2(self):
        py.test.skip('broken test')
        test = ur"""
test

test

"""
        output = ur"""
<p>test </p>
<p>test </p>
"""
        self.do(test, output)

    def testPreSuccess1(self):
        py.test.skip('broken test')
        test = ur"""
{{{
test
}}}

"""
        output = ur"""
<pre>
test
</pre>
"""
        self.do(test, output)

    def testPreSuccess2(self):
        py.test.skip('broken test')
        test = ur"""
{{{
test
test
}}}

"""
        output = ur"""
<pre>
test
test
</pre>
"""
        self.do(test, output)

    def testPreSuccess3(self):
        py.test.skip('broken test')
        test = ur"""
{{{
test

test
}}}

"""
        output = ur"""
<pre>
test

test
</pre>
"""
        self.do(test, output)

    def testPreSuccess4(self):
        py.test.skip('broken test')
        test = ur"""
{{{
 * test
}}}

"""
        output = ur"""
<pre>
 * test
</pre>
"""
        self.do(test, output)

    def testPreSuccess5(self):
        py.test.skip('broken test')
        test = ur"""
{{{
  }}}

"""
        output = ur"""
<pre>
  </pre>
"""
        self.do(test, output)

    def testPreSuccess6(self):
        test = ur"""
 * {{{
test
}}}

"""
        output = ur"""
<ul>
<li>
<pre>
test
</pre>
</li>
</ul>
"""
        self.do(test, output)

    def testPreSuccess7(self):
        test = ur"""
 * {{{
   test
   }}}

"""
        output = ur"""
<ul>
<li>
<pre>
   test
   </pre>
</li>
</ul>
"""
        self.do(test, output)

    def testPreSuccess8(self):
        test = ur"""
 * test
 {{{
test
}}}

"""
        output = ur"""
<ul>
<li><p>test
</p>
<pre>
test
</pre>
</li>
</ul>
"""
        self.do(test, output)

    def testPreSuccess9(self):
        py.test.skip('broken test')
        test = ur"""
 * test

{{{
test
}}}

"""
        output = ur"""
<ul>
<li><p>test </p>
</li>
</ul>

<pre>
test
</pre>
"""
        self.do(test, output)

    def testRule1(self):
        py.test.skip('broken test')
        test = ur"""
----

"""
        output = ur"""
<hr/>
"""
        self.do(test, output)

    def testTable01(self):
        py.test.skip('broken test')
        test = ur"""
|| ||

"""
        output = ur"""
<div>
<table>
<tr>
<td>
<p> </p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable02(self):
        py.test.skip('broken test')
        test = ur"""
||test||

"""
        output = ur"""
<div>
<table>
<tr>
<td>
<p>test</p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable03(self):
        py.test.skip('broken test')
        test = ur"""
||test||test||

"""
        output = ur"""
<table>
<tr>
<td>
<p class="line862">
test
</td>
<td>
<p class="line862">test
</td>
</tr>
</table>
"""
        self.do(test, output)

    def testTable04(self):
        py.test.skip('broken test')
        test = ur"""
||test||
||test||test||

"""
        output = ur"""
<div>
<table>
<tr>
<td>
<p>test</p>
</td>
</tr>
<tr>
<td>
<p>test</p>
</td>
<td>
<p>test</p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable05(self):
        py.test.skip('broken test')
        test = ur"""
||||test||
||test||test||

"""
        output = ur"""
<div>
<table>
<tr>
<td colspan="2" style="text-align: center;">
<p>test</p>
</td>
</tr>
<tr>
<td>
<p>test</p>
</td>
<td>
<p>test</p>
</td>
</tr>
</table>
</div>
"""
        self.do(test, output)

    def testTable06(self):
        py.test.skip('broken test')
        test = ur"""
||||test||test||
||test||||test||

"""
        output = ur"""
<table><tbody><tr>  <td style="text-align: center;"
colspan="2"><p class="line862">test</p></td>   <td><p class="line862">test</p></td>
</tr> <tr>  <td><p class="line862">test</p></td>   <td style="text-align: center;"
colspan="2"><p class="line862">test</p></td> </tr> </tbody></table>"""
        self.do(test, output)

class TestConvertInlineFormatRepeatable(TestBase):
    def do(self, text, output):
        text = text.lstrip('\n')
        output = output.strip('\n')
        output = "<p>%s </p>" % output
        request = MinimalRequest(self.request)
        page = MinimalPage()
        formatter = Formatter(request)
        formatter.setPage(page)
        Parser(text, request).format(formatter)
        repeat = ''.join(request.result).strip('\n')
        #assert repeat == output
        out = self.do_convert_real([request, page.page_name, repeat])
        out = out.rstrip('\n')
        assert text == out

    def testEmphasis01(self):
        py.test.skip('broken test')
        test = ur"''test''"
        output = ur"<em>test</em>"
        self.do(test, output)

    def testEmphasis02(self):
        py.test.skip('broken test')
        test = ur"'''test'''"
        output = ur"<strong>test</strong>"
        self.do(test, output)

    def testEmphasis03(self):
        py.test.skip('broken test')
        test = ur"'''''test'''''"
        output = ur"<em><strong>test</strong></em>"
        self.do(test, output)

    def testEmphasis04(self):
        py.test.skip('broken test')
        test = ur"''test'''test'''''"
        output = ur"<em>test<strong>test</strong></em>"
        self.do(test, output)

    def testEmphasis05(self):
        py.test.skip('broken test')
        test = ur"'''test''test'''''"
        output = ur"<strong>test<em>test</em></strong>"
        self.do(test, output)

    def testEmphasis06(self):
        py.test.skip('broken test')
        test = ur"''test'''test'''test''"
        output = ur"<em>test<strong>test</strong>test</em>"
        self.do(test, output)

    def testEmphasis07(self):
        py.test.skip('broken test')
        test = ur"'''test''test''test'''"
        output = ur"<strong>test<em>test</em>test</strong>"
        self.do(test, output)

    def testEmphasis08(self):
        py.test.skip('broken test')
        test = ur"''test'''''test'''"
        output = ur"<em>test</em><strong>test</strong>"
        self.do(test, output)

    def testEmphasis09(self):
        py.test.skip('broken test')
        test = ur"'''test'''''test''"
        output = ur"<strong>test</strong><em>test</em>"
        self.do(test, output)

    def testEmphasis10(self):
        py.test.skip('broken test')
        test = ur"'''''test''test'''"
        output = ur"<strong><em>test</em>test</strong>"
        self.do(test, output)

    def testEmphasis11(self):
        py.test.skip('broken test')
        test = ur"'''''test'''test''"
        output = ur"<em><strong>test</strong>test</em>"
        self.do(test, output)

    def testFormatBig01(self):
        py.test.skip('broken test')
        test = ur"~+test+~"
        output = ur"<big>test</big>"
        self.do(test, output)

    def testFormatSmall01(self):
        py.test.skip('broken test')
        test = ur"~-test-~"
        output = ur"<small>test</small>"
        self.do(test, output)

    def testFormatStrike01(self):
        py.test.skip('broken test')
        test = ur"--(test)--"
        output = ur"<strike>test</strike>"
        self.do(test, output)

    def testFormatSub01(self):
        py.test.skip('broken test')
        test = ur",,test,,"
        output = ur"<sub>test</sub>"
        self.do(test, output)

    def testFormatSup01(self):
        py.test.skip('broken test')
        test = ur"^test^"
        output = ur"<sup>test</sup>"
        self.do(test, output)

    def testFormatUnderline01(self):
        py.test.skip('broken test')
        test = ur"__test__"
        output = ur"<u>test</u>"
        self.do(test, output)

    def testPre01(self):
        py.test.skip('broken test')
        test = ur"{{{test}}}"
        output = ur"<tt>test</tt>"
        self.do(test, output)

    def testWhitespace01(self):
        py.test.skip('broken test')
        test = ur"''test '''test'''''"
        output = ur"<em>test <strong>test</strong></em>"
        self.do(test, output)

class TestConvertInlineItemRepeatable(TestBase):
    def do(self, text, output):
        text = text.lstrip('\n')
        output = output.strip('\n')
        output = "<p>%s </p>" % output
        request = MinimalRequest(self.request)
        page = MinimalPage()
        formatter = Formatter(request)
        formatter.setPage(page)
        Parser(text, request).format(formatter)
        repeat = ''.join(request.result).strip('\n')
        #assert repeat == output
        out = self.do_convert_real([request, page.page_name, repeat])
        out = out.rstrip('\n')
        assert text == out

    def testWikiWord01(self):
        py.test.skip('broken test')
        test = ur"WikiWord"
        output = ur"""<a class="nonexistent" href="./WikiWord">WikiWord</a>"""
        self.do(test, output)

    def testNoWikiWord01(self):
        py.test.skip('broken test')
        test = ur"!WikiWord"
        output = ur"WikiWord"
        self.do(test, output)

    def testSmiley01(self):
        py.test.skip('broken test')
        test = ur":-)"
        output = ur"""<img src="/wiki/modern/img/smile.png" alt=":-)" height="15" width="15">"""
        self.do(test, output)

class TestStrip(object):
    def do(self, cls, text, output):
        tree = converter.parse(self.request, text)
        cls().do(tree)
        out = StringIO()
        try:
            import xml.dom.ext
        except ImportError:
            py.test.skip('xml.dom.ext module is not available')
        xml.dom.ext.Print(tree, out)
        assert "<?xml version='1.0' encoding='UTF-8'?>%s" % output == out.getvalue().decode("utf-8")

class TestStripWhitespace(TestStrip):
    def do(self, text, output):
        super(TestStripWhitespace, self).do(converter.strip_whitespace, text, output)

    def test1(self):
        test = ur"""
<t/>
"""
        output = ur"""<t/>"""
        self.do(test, output)

    def test2(self):
        py.test.skip('broken test')
        test = ur"""
<t>
  <z/>
</t>
"""
        output = ur"""<t><z/></t>"""
        self.do(test, output)

    def test3(self):
        py.test.skip('broken test')
        test = ur"""
<t>
  <z>test</z>
</t>
"""
        output = ur"""<t><z>test</z></t>"""
        self.do(test, output)

    def test4(self):
        test = ur"""<p>&nbsp;</p>"""
        output = ur""""""
        self.do(test, output)

    def test5(self):
        test = ur"""<p>test </p>"""
        output = ur"""<p>test</p>"""
        self.do(test, output)

class TestConvertBrokenBrowser(TestBase):
    def do(self, text, output):
        text = text.strip('\n')
        output = output.strip()
        request = MinimalRequest(self.request)
        page = MinimalPage()
        out = self.do_convert_real([request, page.page_name, text])
        out = out.strip()

        assert output == out

    def testList01(self):
        test = ur"""
<ul>
<li>test</li>
<ul>
<li>test</li>
</ul>
<li>test</li>
</ul>
"""
        output = ur"""
 * test
  * test
 * test

"""
        self.do(test, output)

class TestConvertImportFromOOo(TestBase):
    def do(self, text, output):
        text = text.strip('\n')
        output = output.strip()
        request = MinimalRequest(self.request)
        page = MinimalPage()
        out = self.do_convert_real([request, page.page_name, text])
        out = out.strip()
        assert output == out

    def testOOoTable01(self):
        # tests cut and paste from OOo to gui (empty cells do have a <br \>
        test = u"""<p class="line874">
        <meta content="text/html; charset=utf-8" http-equiv="CONTENT-TYPE" />
        <title></title><meta content="OpenOffice.org 2.0  (Linux)" name="GENERATOR" />
        <style type="text/css">
        <!--
        BODY,DIV,TABLE,THEAD,TBODY,TFOOT,TR,TH,TD,P { font-family:"Albany AMT"; font-size:x-small }
         -->
        </style>
        <table rules="none" frame="void" cols="4" cellspacing="0" border="0">     <colgroup><col width="86"></col><col width="86"></col><col width="86"></col><col width="86"></col></colgroup>
        <tbody>
        <tr>             <td width="86" height="19" align="left"><font size="3">a</font></td>             <td width="86" valign="middle" align="left" sdnum="1031;0;@"><font size="3" face="Times New Roman">b</font></td>             <td width="86" valign="middle" align="left" sdnum="1031;0;@"><font size="3" face="Times New Roman">c</font></td>             <td width="86" valign="middle" align="left" sdnum="1031;0;@"><font size="3" face="Times New Roman"><br /></font></td>         </tr>
        <tr>             <td valign="middle" height="19" align="left" sdnum="1031;0;@"><font size="3" face="Times New Roman">a</font></td>             <td valign="middle" align="center" sdnum="1031;0;@" colspan="2"><font size="3" face="Times New Roman">b</font></td>             <td valign="middle" align="left" sdnum="1031;0;@"><font size="3" face="Times New Roman">d</font></td>         </tr>
        </tbody>
        </table>  </p>"""

        output = u"""||<( width="86px" height="19px">a||<( width="86px">b||<( width="86px">c||<( width="86px"> <<BR>> ||
||<( height="19px">a||||b||<(>d||"""

        self.do(test, output)

    def testTable02(self):
        # tests empty cells
        test = u"""<table><tbody>
                   <tr>  <td width="86" height="19" style="text-align: left;"><p class="line891"><strong>a</strong></p></td>   <td width="86" style="text-align: left;"><p class="line891"><strong>b</strong></p></td>   <td width="86" style="text-align: left;"><p class="line891"><strong>c</strong></p></td>   <td width="86" style="text-align: left;"><p class="line891"><strong>d</strong></p></td>   <td width="86" style="text-align: left;"><p class="line891"><strong>e</strong></p></td>   <td width="86" style="text-align: left; vertical-align: top;"><p class="line891"><strong>f</strong></p></td>   <td width="86" style="text-align: left; vertical-align: top;"><p class="line891"><strong>g</strong></p></td> </tr>
                   <tr>  <td height="19" style="text-align: left;"><p class="line862">a</p></td>   <td style="text-align: center;" rowspan="2" colspan="4"><p class="line862">b</p></td>   <td style="text-align: center; vertical-align: top;"></td>   <td style="text-align: center; vertical-align: top;"></td> </tr>
                   <tr>  <td height="19" style="text-align: left;"><p class="line862">a</p></td>   <td style="text-align: center;"></td>   <td style="text-align: center; vertical-align: top;"></td> </tr>
                   <tr>  <td height="19" style="text-align: left;"><p class="line862">a</p></td>   <td style="text-align: center;" rowspan="2" colspan="1"><p class="line862">b</p></td>   <td style="text-align: center;" rowspan="2" colspan="1"><p class="line862">c </p></td>   <td style="text-align: left;"><p class="line862">d</p></td>   <td style="text-align: left;"><p class="line862">e</p></td>   <td style="text-align: center;"></td>   <td style="text-align: center; vertical-align: top;"></td> </tr>
                   <tr>  <td height="19" style="text-align: left;"><p class="line862">a</p></td>   <td style="text-align: left;"><p class="line862">d</p></td>   <td style="text-align: left;"><p class="line862">e</p></td>   <td style="text-align: center;"></td>   <td style="text-align: center; vertical-align: top;"></td> </tr>
                   <tr>  <td height="19" style="text-align: left;"><p class="line862">a</p></td>   <td style="text-align: left;"><p class="line862">b</p></td>   <td style="text-align: left;"><p class="line862">c</p></td>   <td style="text-align: left;"><p class="line862">d</p></td>   <td style="text-align: left;"><p class="line862">e</p></td>   <td style="text-align: center;"><p class="line862">f</p></td>   <td style="text-align: center; vertical-align: top;"><p class="line862">g</p></td> </tr>
                   </tbody></table>"""


        output = u"""
||<width="86px" height="19px" style="text-align: left;">'''a''' ||<width="86px" style="text-align: left;">'''b''' ||<width="86px" style="text-align: left;">'''c''' ||<width="86px" style="text-align: left;">'''d''' ||<width="86px" style="text-align: left;">'''e''' ||<width="86px" style="text-align: left; vertical-align: top;">'''f''' ||<width="86px" style="text-align: left; vertical-align: top;">'''g''' ||
||<height="19px" style="text-align: left;">a ||||||||<style="text-align: center;" |2>b ||<style="text-align: center; vertical-align: top;"> ||<style="text-align: center; vertical-align: top;"> ||
||<height="19px" style="text-align: left;">a ||<style="text-align: center;"> ||<style="text-align: center; vertical-align: top;"> ||
||<height="19px" style="text-align: left;">a ||<style="text-align: center;" |2>b ||<style="text-align: center;" |2>c ||<style="text-align: left;">d ||<style="text-align: left;">e ||<style="text-align: center;"> ||<style="text-align: center; vertical-align: top;"> ||
||<height="19px" style="text-align: left;">a ||<style="text-align: left;">d ||<style="text-align: left;">e ||<style="text-align: center;"> ||<style="text-align: center; vertical-align: top;"> ||
||<height="19px" style="text-align: left;">a ||<style="text-align: left;">b ||<style="text-align: left;">c ||<style="text-align: left;">d ||<style="text-align: left;">e ||<style="text-align: center;">f ||<style="text-align: center; vertical-align: top;">g ||"""


        self.do(test, output)

coverage_modules = ['MoinMoin.converter.text_html_text_moin_wiki']

