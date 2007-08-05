# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of wiki content conversion

    TODO:
    * add some ../some_page test
    * add some /some_page test
    * add more quote_triggers
    * fix parser/converter anchor link handling
    * emit a warning if we find some page name that was renamed as a macro argument?
    * shall we support camelcase renaming?

    Limitations of this converter:
    * converter does not touch "pre sections", thus markup examples in {{{ }}}
      or ` ` will have to get handled manually.
    * converter does not touch macro arguments, they will have to get handled
      manually

Remaining problems:

 [wiki:/RecommendPage]
 [wiki:/farms farms]

 [wiki:MacroMarket/EmbedObject EO]
 [wiki:SeaPig/BrianDorsey]            ambiguity!!! can be resolved with some interwiki map lookup
                                      and transformed to wiki:SeaPig:BrianDorsey if SeaPig is in 
                                      interwiki map, but no page SeaPig exists.

 [:MeatBall:CleanLinking meatball-wiki: clean linking]
 [:Infrastructure:Infrastructure] optimize to ["Infrastructure"]
 [attachment:My%20Attachment.jpg:it works]
 [wiki:LinuxWiki: LinuxWiki.de] 

    @copyright: 2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script.migration._conv160_wiki import convert_wiki

def test_wiki_conversion(request):
    pagename = 'TestPage'
    rename_some_page = {
            ('PAGE', 'some_page'): 'some page',
            # NEEDED? ('PAGE', 'RenameThis'): 'ThisRenamed',
    }
    rename_some_file = {
            ('FILE', pagename, 'with_underscore'): 'without underscore',
            ('FILE', pagename, 'with blank'): 'without_blank',
    }
    tests = [
        # NEEDED? ('CamelCase', {}, 'CamelCase'),
        # FAILS ('RenameThis', rename_some_page, 'ThisRenamed'),
        # NEEDED? ('!RenameThis', {}, '!RenameThis'), # not a link

        # "nothing changed" checks
        ('', {}, ''),
        ('MoinMaster:CamelCase', {}, 'MoinMaster:CamelCase'),
        ('some_text', {}, 'some_text'),
        ('["some_text"]', {}, '["some_text"]'),
        ('some_page', rename_some_page, 'some_page'), # not a link
        ('{{{["some_page"]}}}', rename_some_page, '{{{["some_page"]}}}'), # not a link
        ('`["some_page"]`', rename_some_page, '`["some_page"]`'), # not a link
        ('["OtherPage/some_page"]', rename_some_page, '["OtherPage/some_page"]'), # different link
        ('MoinMaster:some_page', rename_some_page, 'MoinMaster:some_page'), # external link
        ('http://some_server/some_page', rename_some_page, 'http://some_server/some_page'), # external link
        ('[http://some_server/some_page]', rename_some_page, '[http://some_server/some_page]'), # external link
        ('[#some_page]', rename_some_page, '[#some_page]'), # link to anchor that has same name
        ('[attachment:some_page.png]', rename_some_page, '[attachment:some_page.png]'), # att, not page
        ('[attachment:some_page.png test picture]', rename_some_page, '[attachment:some_page.png test picture]'), # att, not page
        ('[attachment:some_page.txt attachment:some_page.png]', rename_some_page, '[attachment:some_page.txt attachment:some_page.png]'),

        # page rename changes result
        ('["some_page"]', rename_some_page, '["some page"]'),
        ('[:some_page]', rename_some_page, '["some page"]'),
        ('[:some_page:]', rename_some_page, '["some page"]'),
        ('[:some_page:some text]', rename_some_page, '["some page" some text]'),
        ('Self:some_page', rename_some_page, '["some page"]'),
        ('wiki:Self:some_page', rename_some_page, '["some page"]'),
        ('[wiki:Self:some_page some text]', rename_some_page, '["some page" some text]'),
        # XXX FAILS ('wiki:Self:some_page#some_anchor', rename_some_page, '["some page"#some_anchor]'),

        # other markup changes we do
        ('[:other page]', {}, '["other page"]'),
        ('[:other page:]', {}, '["other page"]'),
        ('[:other page:other text]', {}, '["other page" other text]'),
        # FAILS ('Self:CamelCase', {}, 'CamelCase'),
        ('[wiki:WikiPedia:Lynx_%28web_browser%29 Lynx]', {}, '[wiki:WikiPedia:"Lynx_(web_browser)" Lynx]'),

        # "nothing changed" checks
        ('attachment:OtherPage/with_underscore', rename_some_file, 'attachment:OtherPage/with_underscore'),

        # file rename changes result
        ('attachment:with_underscore', rename_some_file, 'attachment:"without underscore"'),
        ('attachment:TestPage/with_underscore', rename_some_file, 'attachment:"without underscore"'), # remove superfluous pagename

        # attachment syntax: kill %20
        ('attachment:with%20blank', rename_some_file, 'attachment:without_blank'), # plus rename
        ('attachment:keep%20blank', rename_some_file, 'attachment:"keep blank"'), # no rename
        ('attachment:TestPage/keep%20blank', rename_some_file, 'attachment:"keep blank"'), # remove superfluous pagename
        ('attachment:OtherPage/keep%20blank', rename_some_file, 'attachment:"OtherPage/keep blank"'),
    ]
    for data, renames, expected in tests:
        assert convert_wiki(request, pagename, data, renames) == expected

