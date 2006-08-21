# -*- coding: iso-8859-1 -*-
'''
    MoinMoin - AdvancedSearch Macro

    [[AdvancedSearch]]
        displays advanced search dialog.

    MAYBE:
    [[AdvancedSearch(Help)]]
        embed results of an advanced search (use more parameters...)
'''

from MoinMoin import config, wikiutil, search
from MoinMoin.i18n import languages
from MoinMoin.support import sorted

import mimetypes

Dependencies = ['pages']


def advanced_ui(macro):
    _ = macro._
    f = macro.formatter

    search_boxes = ''.join([
        f.table_row(1),
        f.table_cell(1, attrs={'rowspan': '6', 'class': 'searchfor'}),
        f.text(_('Search for pages')),
        f.table_cell(0),
        ''.join([''.join([
            f.table_row(1),
            f.table_cell(1),
            f.text(_(txt)),
            f.table_cell(0),
            f.table_cell(1),
            f.rawHTML(input_field),
            f.table_cell(0),
            f.table_row(0),
        ]) for txt, input_field in (
            (_('containing all the following terms'),
                '<input type="text" name="and_terms" size="30">'),
            (_('containing one or more of the following terms'),
                '<input type="text" name="or_terms" size="30">'),
            (_('not containing the following terms'),
                '<input type="text" name="not_terms" size="30">'),
            #('containing only one of the following terms',
            #    '<input type="text" name="xor_terms" size="30">'),
            # TODO: dropdown-box?
            (_('belonging to one of the following categories'),
                '<input type="text" name="categories" size="30">'),
            (_('last modified since'),
                '<input type="text" name="mtime" size="30" value="">'),
        )])
    ])

    langs = dict([(lang, lmeta['x-language-in-english'])
        for lang, lmeta in languages.items()])
    userlang = macro.request.user.language or \
            macro.request.cfg.language_default
    lang_dropdown = ''.join([
        u'<select name="language" size="1">',
        u'<option value="" selected>%s</option>' % _('any language'),
        ''.join(['<option value="%s">%s</option>' % lt for lt in
            [(userlang, langs[userlang])] + sorted(langs.items(),
                key=lambda i: i[1])]),
        u'</select>',
    ])

    ft_dropdown = ''.join([
        u'<select name="mimetype" size="1">',
        u'<option value="" selected>%s</option>' % _('any type'),
        ''.join(['<option value="%s">%s</option>' % (m[1], '*%s - %s' % m)
            for m in sorted(mimetypes.types_map.items())]),
        u'</select>',
    ])

    search_options = ''.join([
        ''.join([
            f.table_row(1),
            f.table_cell(1, attrs={'class': 'searchfor'}),
            txt[0],
            f.table_cell(0),
            f.table_cell(1, colspan=2),
            txt[1],
            f.table_cell(0),
            f.table_row(0),
            ]) for txt in (
                (_('Language'), lang_dropdown),
                (_('File Type'), ft_dropdown),
                ('', '<input type="checkbox" name="titlesearch" value="1">%s</input>' %
                _('Search only in titles')),
                ('', '<input type="checkbox" name="case" value="1">%s</input>' %
                _('Case-sensitive search')),
                ('', '<input type="checkbox" name="includeunderlay" value="1" checked>%s'
                    '</input>' % _('Include underlay')),
                ('', '<input type="checkbox" name="onlysystempages" value="1">%s'
                    '</input>' % _('Only system pages')),
            )
    ])
    
    html = [
        u'<form method="get" action="">',
        u'<div>',
        u'<input type="hidden" name="action" value="fullsearch">',
        u'<input type="hidden" name="advancedsearch" value="1">',
        f.table(1, attrs={'tableclass': 'advancedsearch'}),
        search_boxes,
        search_options,
        f.table_row(1),
        f.table_cell(1, attrs={'class': 'submit', 'colspan': '3'}),
        u'<input type="submit" value="%s">' % _('Go get it!'),
        f.table_cell(0),
        f.table_row(0),
        f.table(0),
        u'</div>',
        u'</form>',
    ]

    return f.rawHTML('\n'.join(html))


def execute(macro, needle):
    request = macro.request
    _ = request.getText

    # no args given
    if needle is None:
        return advanced_ui(macro)

    return macro.formatter.rawHTML('wooza!')
        

