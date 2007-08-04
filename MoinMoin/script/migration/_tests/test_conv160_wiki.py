# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of wiki content conversion

    @copyright: 2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script.migration._conv160_wiki import convert_wiki

def test_wiki_conversion(request):
    pagename = 'TestPage'
    rename_some_page = {
            ('PAGE', 'some_page'): 'some page',
    }
    rename_some_file = {
            ('FILE', pagename, 'with_underscore'): 'without underscore',
            ('FILE', pagename, 'with blank'): 'without_blank',
    }
    tests = [
        # "nothing changed" checks
        ('', {}, ''),
        ('CamelCase', {}, 'CamelCase'),
        ('MoinMaster:CamelCase', {}, 'MoinMaster:CamelCase'),
        ('some_text', {}, 'some_text'),
        ('["some_text"]', {}, '["some_text"]'),
        ('some_page', rename_some_page, 'some_page'), # not a link

        # page rename changes result
        ('["some_page"]', rename_some_page, '["some page"]'),
        ('[:some_page]', rename_some_page, '["some page"]'),
        ('[:some_page:]', rename_some_page, '["some page"]'),
        ('[:some_page:some text]', rename_some_page, '["some page" some text]'),
        ('Self:some_page', rename_some_page, '["some page"]'),
        ('wiki:Self:some_page', rename_some_page, '["some page"]'),
        ('[wiki:Self:some_page]', rename_some_page, '["some page"]'),
        ('[wiki:Self:some_page some text]', rename_some_page, '["some page" some text]'),

        # other markup changes we do
        ('[:other page]', {}, '["other page"]'),
        ('[:other page:]', {}, '["other page"]'),
        ('[:other page:other text]', {}, '["other page" other text]'),
        # FAILS ('Self:CamelCase', {}, 'CamelCase'),

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

