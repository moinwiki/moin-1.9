# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of wiki content conversion

    TODO:
    * fix failing tests
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

from MoinMoin import i18n
i18n_wikiLanguages = i18n.wikiLanguages
# convert_wiki overwrites i18n.wikiLanguages, we revert this change for following tests
from MoinMoin.script.migration._conv160_wiki import convert_wiki
i18n.wikiLanguages = i18n_wikiLanguages

class TestWikiConversion:
    """ test the wiki markup conversion 1.5.8 -> 1.6.0 """
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
            # FAILING tests:
            # does not work in 1.5.8, no need to convert:
            #('[:MeatBall:CleanLinking meatball-wiki: clean linking]', {}, '[:MeatBall:CleanLinking meatball-wiki: clean linking]'),

            # does not work in 1.5.8, no need to convert:
            #('[attachment:some_page.txt attachment:some_page.png]', rename_some_page, '[[attachment:some_page.txt|{{attachment:some_page.png}}]]'),

            # "nothing changed" checks (except markup)
            ('', {}, ''),
            ('CamelCase', {}, 'CamelCase'),
            ('MoinMaster:CamelCase', {}, 'MoinMaster:CamelCase'),
            ('[wiki:LinuxWiki: LinuxWiki.de]', {}, '[[LinuxWiki:|LinuxWiki.de]]'),
            # does not work in 1.5.8, no need to convert:
            #('[wiki:MacroMarket/EmbedObject EO]', {}, '["MacroMarket/EmbedObject" EO]'),
            ('[wiki:MoinMoin/FrontPage]', {}, 'MoinMoin:FrontPage'),
            ('[wiki:/OtherPage]', rename_some_page, '[[/OtherPage]]'),
            ('[wiki:/OtherPage other page]', rename_some_page, '[[/OtherPage|other page]]'),
            ('some_text', {}, 'some_text'),
            ('["some_text"]', {}, '[[some_text]]'),
            ('some_page', rename_some_page, 'some_page'), # not a link
            ('{{{["some_page"]}}}', rename_some_page, '{{{["some_page"]}}}'), # not a link
            ('`["some_page"]`', rename_some_page, '`["some_page"]`'), # not a link
            ('["OtherPage/some_page"]', rename_some_page, '[[OtherPage/some_page]]'), # different link
            ('MoinMaster:some_page', rename_some_page, 'MoinMaster:some_page'), # external link
            ('http://some_server/some_page', rename_some_page, 'http://some_server/some_page'), # external link
            ('[http://some_server/some_page]', rename_some_page, '[[http://some_server/some_page]]'), # external link
            ('[#some_page]', rename_some_page, '[[#some_page]]'), # link to anchor that has same name
            ('[attachment:some_page.png]', rename_some_page, '[[attachment:some_page.png]]'), # att, not page
            ('[attachment:some_page.png test picture]', rename_some_page, '[[attachment:some_page.png|test picture]]'), # att, not page
            # url unquote stuff (%20 was popular for space)
            ('attachment:My%20Attachment.jpg', {}, '{{attachment:My Attachment.jpg}}'), # embed!
            ('[attachment:My%20Attachment.jpg]', {}, '[[attachment:My Attachment.jpg]]'), # link!
            ('[attachment:My%20Attachment.jpg it works]', {}, '[[attachment:My Attachment.jpg|it works]]'),

            # page rename changes result
            ('["some_page"]', rename_some_page, '[[some page]]'),
            ('[:some_page]', rename_some_page, '[[some page]]'),
            ('[:some_page:]', rename_some_page, '[[some page]]'),
            ('[:some_page:some text]', rename_some_page, '[[some page|some text]]'),
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

            # attachment syntax: kill %20
            ('attachment:with%20blank', rename_some_file, '[[attachment:without_blank]]'), # plus rename
            ('attachment:keep%20blank', rename_some_file, '[[attachment:keep blank]]'), # no rename
            ('attachment:TestPage/keep%20blank', rename_some_file, '[[attachment:keep blank]]'), # remove superfluous pagename
            ('attachment:OtherPage/keep%20blank', rename_some_file, '[[attachment:OtherPage/keep blank]]'),

            # embed images
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

    def test_parser(self):
        #py.test.skip("not wanted right now")
        markup_15 = u"""\
{{{#!html
...
}}}

"""
        expected_markup_160 = u"""\
{{{#!html
...
}}}

"""
        markup_160 = convert_wiki(self.request, u'TestPage', markup_15, {})
        #print markup_15 ; print "---" ; print markup_160
        markup_160 = markup_160.replace('\r\n', '\n')
        assert markup_160 == expected_markup_160


    def test_pre(self):
        #py.test.skip("not wanted right now")
        markup_15 = u"""\
{{{
...
}}}

"""
        expected_markup_160 = u"""\
{{{
...
}}}

"""
        markup_160 = convert_wiki(self.request, u'TestPage', markup_15, {})
        #print markup_15 ; print "---" ; print markup_160
        markup_160 = markup_160.replace('\r\n', '\n')
        assert markup_160 == expected_markup_160

