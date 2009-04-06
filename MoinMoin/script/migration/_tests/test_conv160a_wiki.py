# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of wiki content conversion

    TODO:
    * fix parser/converter anchor link handling
    * emit a warning if we find some page name that was renamed as a macro argument?
    * shall we support camelcase renaming?

    Limitations of this converter:
    * converter does not touch "pre sections", thus markup examples in {{{ }}}
      or ` ` will have to get handled manually.
    * converter does not touch macro arguments, they will have to get handled
      manually
    * converter does not touch CamelCase links (but there should be no need to do)

    @copyright: 2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import py
#py.test.skip("broken")

from MoinMoin.script.migration._conv160a_wiki import convert_wiki

class TestWikiConversion:
    """ test the wiki markup conversion 1.6.0a -> 1.6.0 """
    def test_absolute(self):
        request = self.request
        pagename = 'TestPage'
        rename_some_page = {
                ('PAGE', 'some_page'): 'some page',
        }
        rename_some_file = {
                ('FILE', pagename, 'with_underscore'): 'without underscore',
                ('FILE', pagename, 'with blank'): 'without_blank',
        }

        tests = [
            # attachment links
            ("attachment:filename.ext", {}, "[[attachment:filename.ext]]"),
            ("[attachment:'Filename.ext' Aliasname]", {}, "[[attachment:Filename.ext|Aliasname]]"),
            ("[attachment:'Pagename/Filename.ext' Aliasname]", {}, "[[attachment:Pagename/Filename.ext|Aliasname]]"),
            ("[attachment:'Pagename/Subpage/Filename.ext' Aliasname]", {}, "[[attachment:Pagename/Subpage/Filename.ext|Aliasname]]"),
            ('[attachment:"Pagename/Subpage/File Name.ext" Aliasname]', {}, "[[attachment:Pagename/Subpage/File Name.ext|Aliasname]]"),
            ('[inline:text.txt]', {}, '{{attachment:text.txt}}'), # inline is now implied by {{...}}
            ('[inline:image.jpg]', {}, '{{attachment:image.jpg}}'), # inline is now implied by {{...}}
            ('[drawing:image]', {}, '{{drawing:image}}'),
            ('[inline:text.txt foo]', {}, '{{attachment:text.txt|foo}}'), # inline is now implied by {{...}}
            ('[inline:image.jpg foo]', {}, '{{attachment:image.jpg|foo}}'), # inline is now implied by {{...}}
            ('[drawing:image foo]', {}, '{{drawing:image|foo}}'),

            # "nothing changed" checks (except markup)
            ('', {}, ''),
            ('CamelCase', {}, 'CamelCase'),
            ('["/Subpage"]', {}, "[[/Subpage]]"),
            ('["Pagename/Subpage"]', {}, "[[Pagename/Subpage]]"),
            ("['Pagename/Subpage' Aliasname]", {}, "[[Pagename/Subpage|Aliasname]]"),
            ('["some page" somepage]', {}, '[[some page|somepage]]'),
            ("['some page' somepage]", {}, '[[some page|somepage]]'),

            ('Doesnotexist:CamelCase', {}, 'Doesnotexist:CamelCase'),
            ('MoinMaster:CamelCase', {}, 'MoinMaster:CamelCase'),
            ("MoinMaster:'some page'", {}, '[[MoinMaster:some page]]'),
            ('MoinMaster:"some page"', {}, '[[MoinMaster:some page]]'),

            ('[wiki:MoinMoin/FrontPage]', {}, 'MoinMoin:FrontPage'),
            ('some_text', {}, 'some_text'),
            ('["some_text"]', {}, '[[some_text]]'),
            ('some_page', rename_some_page, 'some_page'), # not a link
            ('{{{["some_page"]}}}', rename_some_page, '{{{["some_page"]}}}'), # not a link
            ('`["some_page"]`', rename_some_page, '`["some_page"]`'), # not a link
            ('["OtherPage/some_page"]', rename_some_page, '[[OtherPage/some_page]]'), # different link
            ('MoinMaster:some_page', rename_some_page, 'MoinMaster:some_page'), # external link
            ('http://some_server/some_page', rename_some_page, 'http://some_server/some_page'), # external link
            ('[http://some_server/some_page]', rename_some_page, '[[http://some_server/some_page]]'), # external link
            ('[http://some_server/some_page foo]', rename_some_page, '[[http://some_server/some_page|foo]]'), # external link
            ('[#some_page]', rename_some_page, '[[#some_page]]'), # link to anchor that has same name
            ('[attachment:some_page.png]', rename_some_page, '[[attachment:some_page.png]]'), # att, not page
            ('[attachment:some_page.png test picture]', rename_some_page, '[[attachment:some_page.png|test picture]]'), # att, not page

            # page rename changes result
            ('["some_page"]', rename_some_page, '[[some page]]'),
            ('[:some_page]', rename_some_page, '[[some page]]'),
            ('[:some_page#anchor]', rename_some_page, '[[some page#anchor]]'),
            ('[:some_page:]', rename_some_page, '[[some page]]'),
            ('[:some_page#anchor:]', rename_some_page, '[[some page#anchor]]'),
            ('[:some_page:some text]', rename_some_page, '[[some page|some text]]'),
            ('[:some_page#anchor:some text]', rename_some_page, '[[some page#anchor|some text]]'),
            ('Self:some_page', rename_some_page, '[[some page]]'),
            ('wiki:Self:some_page', rename_some_page, '[[some page]]'),
            ('[wiki:Self:some_page some text]', rename_some_page, '[[some page|some text]]'),
            ('wiki:Self:some_page#some_anchor', rename_some_page, '[[some page#some_anchor]]'),

            # other markup changes we do
            ('[:other page]', {}, '[[other page]]'),
            ('[:other page:]', {}, '[[other page]]'),
            ('[:other page:other text]', {}, '[[other page|other text]]'),
            ('Self:CamelCase', {}, 'CamelCase'),
            ('[wiki:WikiPedia:Lynx_%28web_browser%29 Lynx]', {}, '[[WikiPedia:Lynx_(web_browser)|Lynx]]'),
            ('[:Something:Something]', {}, '[[Something]]'), # optimize markup

            # "nothing changed" checks
            ('attachment:OtherPage/with_underscore', rename_some_file, '[[attachment:OtherPage/with_underscore]]'),

            # file rename changes result
            ('attachment:with_underscore', rename_some_file, '[[attachment:without underscore]]'),
            ('attachment:TestPage/with_underscore', rename_some_file, '[[attachment:without underscore]]'), # remove superfluous pagename

            # embed images, all verified on 160a
            ('http://server/image.png', {}, '{{http://server/image.png}}'),
            ('attachment:image.gif', {}, '{{attachment:image.gif}}'),
            ('inline:image.jpg', {}, '{{attachment:image.jpg}}'), # inline is now implied by {{...}}
            ('drawing:image', {}, '{{drawing:image}}'),

            # macros
            ('[[BR]]', {}, '<<BR>>'),
            ('[[FullSearch(wtf)]]', {}, '<<FullSearch(wtf)>>'),
            (u'[[ImageLink(töst.png)]]', {}, u'[[attachment:töst.png|{{attachment:töst.png}}]]'),
            ('[[ImageLink(test.png,OtherPage)]]', {}, '[[OtherPage|{{attachment:test.png}}]]'),
            ('[[ImageLink(test.png,OtherPage,width=123,height=456)]]', {}, '[[OtherPage|{{attachment:test.png||width=123, height=456}}]]'),
            ('[[ImageLink(test.png,OtherPage,width=123,height=456,alt=alttext)]]', {}, '[[OtherPage|{{attachment:test.png|alttext|width=123, height=456}}]]'),
            ('[[ImageLink(test.png,OtherPage,width=123,height=456,alt=alt text with blanks)]]', {}, '[[OtherPage|{{attachment:test.png|alt text with blanks|width=123, height=456}}]]'),
            ('[[ImageLink(http://server/test.png,OtherPage,width=123,height=456)]]', {}, '[[OtherPage|{{http://server/test.png||width=123, height=456}}]]'),
            ('[[ImageLink(http://server/test.png,http://server/,width=123)]]', {}, '[[http://server/|{{http://server/test.png||width=123}}]]'),
            ('[[ImageLink(test.png,attachment:test.png)]]', {}, '[[attachment:test.png|{{attachment:test.png}}]]'),
            ('[[ImageLink(test.png,inline:test.py)]]', {}, '[[attachment:test.py|{{attachment:test.png}}]]'),

        ]
        for data, renames, expected in tests:
            assert convert_wiki(request, pagename, data, renames) == expected

    def test_sisterpage(self):
        request = self.request
        top_page = 'toppage'
        pagename = '%s/subpage' % top_page
        rename_some_page = {
                ('PAGE', '%s/sister' % top_page): '%s/renamed_sister' % top_page,
        }
        tests = [
            # "nothing changed" checks
            ('["../sister_norename"]', rename_some_page, '[[../sister_norename]]'),

            # renames
            ('["../sister"]', rename_some_page, '[[../renamed_sister]]'),
        ]
        for data, renames, expected in tests:
            assert convert_wiki(request, pagename, data, renames) == expected

    def test_subpage(self):
        request = self.request
        pagename = 'toppage'
        rename_some_page = {
                ('PAGE', '%s/subpage' % pagename): '%s/renamed_subpage' % pagename,
        }
        tests = [
            # "nothing changed" checks
            ('["/subpage_norename"]', rename_some_page, '[[/subpage_norename]]'),

            # renames
            ('["/subpage"]', rename_some_page, '[[/renamed_subpage]]'),
        ]
        for data, renames, expected in tests:
            assert convert_wiki(request, pagename, data, renames) == expected

    def test_full_page(self):
        #py.test.skip("not wanted right now")
        markup_160a = u"""\
= CamelCase =
== Pages ==
 1. SomePage
 2. TestPage (does not link to current page)
 3. SomePage/SubPage

## not supported on 160a
##== Pages with anchor ==
## 1. SomePage#anchor
## 2. TestPage#anchor
## 3. SomePage/SubPage#anchor

= Interwiki =
== Pages ==
 1. Self:SomePage
 2. Self:some_page
 3. Self:'some page'
 4. Self:"some page"
 5. MoinMoin:SomePage
 6. MoinMoin:some_page
 7. MoinMoin:'some page'
 8. MoinMoin:"some page"

== Pages with anchor ==
 1. Self:SomePage#anchor
 2. Self:some_page#anchor
 3. Self:'some page#anchor'
 4. Self:"some page#anchor"
 5. MoinMoin:SomePage#anchor
 6. MoinMoin:some_page#anchor
 7. MoinMoin:'some page#anchor'
 8. MoinMoin:"some page#anchor"

== Invalid wiki name ==
 1. Doesnotexist:CamelCase (shall not link)
 2. Foo:bar (shall not link)

= URL =
== simple ==
 1. http://moinmo.in/MoinMoin
 2. http://static.moinmo.in/logos/moinmoin.png (renders image in 160a)
 3. mailto:someone@example.org
 4. wiki:Self:some_page

== with anchor ==
 1. http://moinmo.in/MoinMoin#anchor
 2. wiki:Self:some_page#anchor

= bracketed link =
== Page ==
 1. ["some page"]
 2. ["some page" somepage]
 3. ['some page' somepage]
 4. ["/Subpage"]
 5. ["SomePage/Subpage"]
 6. ['SomePage/Subpage' Some Page]

== Page with anchor ==
 1. ["some page#anchor"]
 2. ["some page#anchor" somepage]
 3. ['some page#anchor' somepage]
 4. ["/Subpage#anchor"]
 5. ["SomePage/Subpage#anchor"]
 6. ['SomePage/Subpage#anchor' Some Page]

== Anchor on current page ==
 1. [#anchor]
## 1. [TestPage#anchor]  not supported on 160a

== URL ==
 1. [http://some_server/some_page]
 2. [http://some_server/some_page some page]
 3. [wiki:MoinMoin/FrontPage]
 4. [wiki:Self:some_page some page]
 5. [wiki:WikiPedia:Lynx_(web_browser) Lynx]
 6. [:some_page]
 7. [:some_page:]
 8. [:some_page:some page]
 9. [:Something:Something]

== URL with anchor ==
 1. [http://some_server/some_page#anchor]
 2. [http://some_server/some_page#anchor some page]
 3. [wiki:MoinMoin/FrontPage#anchor]
 4. [wiki:Self:some_page#anchor some page]
 5. [wiki:WikiPedia:Lynx_(web_browser)#anchor Lynx]
 6. [:some_page#anchor]
 7. [:some_page#anchor:]
 8. [:some_page#anchor:some page]
 9. [:Something#anchor:Something]

= preformatted =
 1. {{{["some_page"]}}} (converter shall not change pre content)
 2. `["some_page"]` (converter shall not change pre content)

= Attachments, Drawings, Images =
== simple ==
 1. attachment:text.txt is linking
 2. inline:text.txt is embedding
 3. attachment:image.png is embedding
 4. inline:image.png is embedding
 5. drawing:image is embedding

== bracketed ==
 1. [attachment:text.txt] is linking
 2. [inline:text.txt] is embedding
 3. [attachment:image.png] is linking
 4. [drawing:image] is embedding png image
 5. [inline:image.png] is showing binary content as text in 160a (wrong)

== bracketed with label ==
 1. [attachment:text.txt some label] is linking
 2. [inline:text.txt some label] is embedding
 3. [attachment:image.png some label] is linking
 4. [drawing:image some label] is embedding png image
 5. [inline:image.png some label] is showing binary content as text in 160a (wrong)

== bracketed, on other page, with label ==
 1. [attachment:SomePage/text.txt some label] is linking
 2. [inline:SomePage/text.txt some label] is embedding
 3. [attachment:SomePage/image.png some label] is linking
 4. [drawing:SomePage/image some label] is embedding png image
 5. [inline:SomePage/image.png some label] is showing binary content as text in 160a (wrong)

"""
        expected_markup_160 = u"""\
= CamelCase =
== Pages ==
 1. SomePage
 2. TestPage (does not link to current page)
 3. [[SomePage/SubPage]]

## not supported on 160a
##== Pages with anchor ==
## 1. SomePage#anchor
## 2. TestPage#anchor
## 3. SomePage/SubPage#anchor

= Interwiki =
== Pages ==
 1. SomePage
 2. [[some_page]]
 3. [[some page]]
 4. [[some page]]
 5. MoinMoin:SomePage
 6. MoinMoin:some_page
 7. [[MoinMoin:some page]]
 8. [[MoinMoin:some page]]

== Pages with anchor ==
 1. [[SomePage#anchor]]
 2. [[some_page#anchor]]
 3. [[some page#anchor]]
 4. [[some page#anchor]]
 5. MoinMoin:SomePage#anchor
 6. MoinMoin:some_page#anchor
 7. [[MoinMoin:some page#anchor]]
 8. [[MoinMoin:some page#anchor]]

== Invalid wiki name ==
 1. Doesnotexist:CamelCase (shall not link)
 2. Foo:bar (shall not link)

= URL =
== simple ==
 1. http://moinmo.in/MoinMoin
 2. {{http://static.moinmo.in/logos/moinmoin.png}} (renders image in 160a)
 3. mailto:someone@example.org
 4. [[some_page]]

== with anchor ==
 1. http://moinmo.in/MoinMoin#anchor
 2. [[some_page#anchor]]

= bracketed link =
== Page ==
 1. [[some page]]
 2. [[some page|somepage]]
 3. [[some page|somepage]]
 4. [[/Subpage]]
 5. [[SomePage/Subpage]]
 6. [[SomePage/Subpage|Some Page]]

== Page with anchor ==
 1. [[some page#anchor]]
 2. [[some page#anchor|somepage]]
 3. [[some page#anchor|somepage]]
 4. [[/Subpage#anchor]]
 5. [[SomePage/Subpage#anchor]]
 6. [[SomePage/Subpage#anchor|Some Page]]

== Anchor on current page ==
 1. [[#anchor]]
## 1. [TestPage#anchor]  not supported on 160a

== URL ==
 1. [[http://some_server/some_page]]
 2. [[http://some_server/some_page|some page]]
 3. MoinMoin:FrontPage
 4. [[some_page|some page]]
 5. [[WikiPedia:Lynx_(web_browser)|Lynx]]
 6. [[some_page]]
 7. [[some_page]]
 8. [[some_page|some page]]
 9. [[Something]]

== URL with anchor ==
 1. [[http://some_server/some_page#anchor]]
 2. [[http://some_server/some_page#anchor|some page]]
 3. MoinMoin:FrontPage#anchor
 4. [[some_page#anchor|some page]]
 5. [[WikiPedia:Lynx_(web_browser)#anchor|Lynx]]
 6. [[some_page#anchor]]
 7. [[some_page#anchor]]
 8. [[some_page#anchor|some page]]
 9. [[Something#anchor|Something]]

= preformatted =
 1. {{{["some_page"]}}} (converter shall not change pre content)
 2. `["some_page"]` (converter shall not change pre content)

= Attachments, Drawings, Images =
== simple ==
 1. [[attachment:text.txt]] is linking
 2. {{attachment:text.txt}} is embedding
 3. {{attachment:image.png}} is embedding
 4. {{attachment:image.png}} is embedding
 5. {{drawing:image}} is embedding

== bracketed ==
 1. [[attachment:text.txt]] is linking
 2. {{attachment:text.txt}} is embedding
 3. [[attachment:image.png]] is linking
 4. {{drawing:image}} is embedding png image
 5. {{attachment:image.png}} is showing binary content as text in 160a (wrong)

== bracketed with label ==
 1. [[attachment:text.txt|some label]] is linking
 2. {{attachment:text.txt|some label}} is embedding
 3. [[attachment:image.png|some label]] is linking
 4. {{drawing:image|some label}} is embedding png image
 5. {{attachment:image.png|some label}} is showing binary content as text in 160a (wrong)

== bracketed, on other page, with label ==
 1. [[attachment:SomePage/text.txt|some label]] is linking
 2. {{attachment:SomePage/text.txt|some label}} is embedding
 3. [[attachment:SomePage/image.png|some label]] is linking
 4. {{drawing:SomePage/image|some label}} is embedding png image
 5. {{attachment:SomePage/image.png|some label}} is showing binary content as text in 160a (wrong)

"""
        markup_160 = convert_wiki(self.request, u'TestPage', markup_160a, {})
        #print markup_160a ; print "---" ; print markup_160
        markup_160 = markup_160.replace('\r\n', '\n')
        assert markup_160 == expected_markup_160

    def test_parser(self):
        markup_160a = u"""\
{{{#!html
...
}}}

"""
        expected_markup_160 = u"""\
{{{#!html
...
}}}

"""
        markup_160 = convert_wiki(self.request, u'TestPage', markup_160a, {})
        #print markup_160a ; print "---" ; print markup_160
        markup_160 = markup_160.replace('\r\n', '\n')
        assert markup_160 == expected_markup_160

    def test_pre(self):
        markup_160a = u"""\
{{{
...
}}}

"""
        expected_markup_160 = u"""\
{{{
...
}}}

"""
        markup_160 = convert_wiki(self.request, u'TestPage', markup_160a, {})
        #print markup_160a ; print "---" ; print markup_160
        markup_160 = markup_160.replace('\r\n', '\n')
        assert markup_160 == expected_markup_160

