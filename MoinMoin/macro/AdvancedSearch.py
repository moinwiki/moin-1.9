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

Dependencies = ['pages']

try:
    sorted
except NameError:
    def sorted(l, *args, **kw):
        l = l[:]
        l.sort(*args, **kw)
        return l

def advanced_ui(macro):
    _ = macro._
    f = macro.formatter

    search_boxes = ''.join([
        f.table_row(1),
        f.table_cell(1, attrs={'rowspan': '7', 'class': 'searchfor'}),
        f.text(_('Search for pages')),
        f.table_cell(0),
        ''.join([''.join([
            f.table_row(1),
            f.table_cell(1),
            f.text('%s:' % _(txt)),
            f.table_cell(0),
            f.table_cell(1),
            f.rawHTML(input_field),
            f.table_cell(0),
            f.table_row(0),
        ]) for txt, input_field in (
            ('containing all the following terms',
                '<input type="text" name="all_terms" size="30">'),
            ('containing one or more of the following '
                'terms', '<input type="text" name="or_terms" size="30">'),
            ('not containing the following terms',
                '<input type="text" name="not_terms" size="30">'),
            ('containing only one of the following terms',
                '<input type="text" name="xor_terms" size="30">'),
            # TODO: dropdown-box?
            ('belonging to one of the following categories',
                '<input type="text" name="categories" size="30">'),
            ('edited since/until the following date',
                '<input type="text" name="date" size="30" value="now">'),
        )])
    ])

    langs = dict([(lang, lmeta['x-language-in-english'])
        for lang, lmeta in sorted(languages.items())])
    lang_dropdown = ''.join([
        u'<select name="language" size="1">',
        u'<option value="" selected>%s</option>' % _('any language'),
        ''.join(['<option value="%s">%s</option>' % lt for lt in
            langs.items()]),
        u'</select>',
    ])

    import mimetypes
    ft_dropdown = ''.join([
        u'<select name="language" size="1">',
        u'<option value="" selected>%s</option>' % _('any type'),
        ''.join(['<option value="%s">%s</option>' % (m[1], '*%s - %s' % m)
            for m in sorted(mimetypes.types_map.items())]),
        u'</select>',
    ])

    search_options = ''.join([
        ''.join([
            f.table_row(1),
            f.table_cell(1, colspan=3),
            txt,
            f.table_cell(0),
            f.table_row(0),
            ]) for txt in (
                'Language: ' + lang_dropdown,
                'File Type: ' + ft_dropdown,
                '<input type="checkbox" name="titlesearch" value="1">%s</input>' %
                _('Search only in titles'),
                '<input type="checkbox" name="case" value="1">%s</input>' %
                _('Case-sensitive search'))
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
        

