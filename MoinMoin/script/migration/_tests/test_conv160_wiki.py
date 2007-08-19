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

from MoinMoin.script.migration._conv160_wiki import convert_wiki

class TestWikiConversion:
    """ test the wiki markup conversion for 1.6.0 """
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
            #('[wiki:/OtherPage]', rename_some_page, '[[/OtherPage]]'),
            #('[wiki:/OtherPage other page]', rename_some_page, '[wiki:/OtherPage other page]'),
            #('[attachment:My%20Attachment.jpg:it works]', {}, '[[attachment:My Attachment.jpg|it works]]'),
            #('[wiki:LinuxWiki: LinuxWiki.de]', {}, '[wiki:LinuxWiki: LinuxWiki.de]'),
            #('[:MeatBall:CleanLinking meatball-wiki: clean linking]', {}, '[:MeatBall:CleanLinking meatball-wiki: clean linking]'),

            # ambiguity!!! can be resolved with some interwiki map lookup
            # and transformed to wiki:MoinMoin:FrontPage if MoinMoin is in
            # interwiki map, but no page MoinMoin exists.
            #('[wiki:MacroMarket/EmbedObject EO]', {}, '["MacroMarket/EmbedObject" EO]'),
            ('[wiki:MoinMoin/FrontPage]', {}, '[[MoinMoin:FrontPage]]'),

            # "nothing changed" checks (except markup)
            ('', {}, ''),
            ('CamelCase', {}, 'CamelCase'),
            ('MoinMaster:CamelCase', {}, 'MoinMaster:CamelCase'),
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
            ('[attachment:some_page.png]', rename_some_page, '{{attachment:some_page.png|some_page}}'), # att, not page
            ('[attachment:some_page.png test picture]', rename_some_page, '{{attachment:some_page.png|test picture}}'), # att, not page
            #('[attachment:some_page.txt attachment:some_page.png]', rename_some_page, '[[attachment:some_page.txt|{{attachment:some_page.png}}]]'),

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
            ('http://server/image.png', {}, '{{http://server/image.png|image}}'),
            ('attachment:image.gif', {}, '{{attachment:image.gif|image}}'),
            ('inline:image.jpg', {}, '{{attachment:image.jpg|image}}'), # inline is now implied by {{...}}
            ('drawing:image', {}, '{{drawing:image}}'),

            # macros
            ('[[BR]]', {}, '<<BR>>'),

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
            # FAILS, see TODO in _replace:
            #('["../sister"]', rename_some_page, '["../renamed_sister"]'),
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
            # FAILS, see TODO in _replace:
            #('["/subpage"]', rename_some_page, '["/renamed_subpage"]'),
        ]
        for data, renames, expected in tests:
            assert convert_wiki(request, pagename, data, renames) == expected


