# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - AdvancedSearch Macro

    [[AdvancedSearch]]
        displays advanced search dialog.
"""

from MoinMoin import config, wikiutil, search
from MoinMoin.i18n import languages
from MoinMoin.support import sorted

import mimetypes

Dependencies = ['pages']


def form_get(request, name, default=''):
    """ Fetches a form field
    
    @param request: current request
    @param name: name of the field
    @keyword default: value if not present (default: '')
    """
    return request.form.get(name, [default])[0]


def advanced_ui(macro):
    """ Returns the code for the advanced search user interface

    @param macro: current macro instance
    """
    _ = macro._
    f = macro.formatter
    request = macro.request

    disabledIfMoinSearch = not request.cfg.xapian_search and \
            ' disabled="disabled"' or ''

    search_boxes = ''.join([
        f.table_row(1),
        f.table_cell(1, attrs={'rowspan': '6', 'class': 'searchfor'}),
        f.text(_('Search for items')),
        f.table_cell(0),
        ''.join([''.join([
            f.table_row(1),
            f.table_cell(1),
            f.text(txt),
            f.table_cell(0),
            f.table_cell(1),
            f.rawHTML(input_field),
            f.table_cell(0),
            f.table_row(0),
        ]) for txt, input_field in (
            (_('containing all the following terms'),
                '<input type="text" name="and_terms" size="30" value="%s">'
                % (form_get(request, 'and_terms') or form_get(request, 'value'))),
            (_('containing one or more of the following terms'),
                '<input type="text" name="or_terms" size="30" value="%s">'
                % form_get(request, 'or_terms')),
            (_('not containing the following terms'),
                '<input type="text" name="not_terms" size="30" value="%s">'
                % form_get(request, 'not_terms')),
            #('containing only one of the following terms',
            #    '<input type="text" name="xor_terms" size="30" value="%s">'
            #    % form_get(request, 'xor_terms')),
            # TODO: dropdown-box?
            (_('belonging to one of the following categories'),
                '<input type="text" name="categories" size="30" value="%s">'
                % form_get(request, 'categories')),
            (_('last modified since (e.g. last 2 weeks)'),
                '<input type="text" name="mtime" size="30" value="%s">'
                % form_get(request, 'mtime')),
        )])
    ])

    # language selection
    searchedlang = form_get(request, 'language')
    langs = dict([(lang, lmeta['x-language-in-english'])
        for lang, lmeta in languages.items()])
    userlang = macro.request.lang
    lang_dropdown = ''.join([
        u'<select name="language" size="1">',
        u'<option value=""%s>%s</option>' %
            (not searchedlang and ' selected' or '', _('any language')),
        ''.join(['<option value="%s"%s>%s</option>' %
                (lt[0], lt[0] == searchedlang and ' selected' or '', lt[1])
            for lt in [(userlang, langs[userlang])] + sorted(langs.items(),
                key=lambda i: i[1])]),
        u'</select>',
    ])

    # mimetype selection
    mimetype = form_get(request, 'mimetype')
    ft_dropdown = ''.join([
        u'<select name="mimetype" size="1"%s>' % disabledIfMoinSearch,
        u'<option value=""%s>%s</option>' %
            (not mimetype and ' selected' or '', _('any type')),
        ''.join(['<option value="%s"%s>%s</option>' %
                (m[1], mimetype == m[1] and ' selected' or '', '*%s - %s' % m)
            for m in sorted(mimetypes.types_map.items())]),
        u'</select>',
    ])

    # misc search options (checkboxes)
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
                ('', '<input type="checkbox" name="titlesearch" '
                    'value="1"%s>%s</input>' %
                (form_get(request, 'titlesearch') and ' checked' or '',
                    _('Search only in titles'))),
                ('', '<input type="checkbox" name="case" '
                    'value="1"%s>%s</input>' %
                (form_get(request, 'case') and ' checked' or '',
                    _('Case-sensitive search'))),
                ('', '<input type="checkbox" name="excludeunderlay" '
                    'value="1"%s>%s</input>' %
                (form_get(request, 'excludeunderlay') and ' checked' or '',
                    _('Exclude underlay'))),
                ('', '<input type="checkbox" name="nosystemitems" '
                    'value="1"%s>%s</input>' %
                (form_get(request, 'nosystemitems') and ' checked' or '',
                    _('No system items'))),
                ('', '<input type="checkbox" name="historysearch" '
                    'value="1"%s%s>%s</input>' %
                (form_get(request, 'historysearch') and ' checked' or '',
                    (not request.cfg.xapian_search or
                     not request.cfg.xapian_index_history) and
                        ' disabled="disabled"' or '',
                     _('Search in all page revisions')))
            )
    ])

    # the dialogue
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
    # for now, just show the advanced ui
    return advanced_ui(macro)

