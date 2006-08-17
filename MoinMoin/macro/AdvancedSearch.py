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

Dependencies = ['pages']

def advanced_ui(macro):
    _ = macro._
    f = macro.formatter

    search_boxes = ''.join([
        ''.join([
            f.table_row(1),
            f.table_cell(1),
            f.text('%s:' % _(txt)),
            f.table_cell(0),
            f.table_cell(1),
            f.rawHTML(input_field),
            f.table_cell(0),
            f.table_row(0),
        ]) for txt, input_field in (
            ('Search for pages containing all the following terms',
                '<input type="text" name="all_terms" size="30">'),
            ('Search for pages containing one or more of the following '
                'terms', '<input type="text" name="or_terms" size="30">'),
            ('Search for pages not containing the following terms',
                '<input type="text" name="not_terms" size="30">'),
            ('Search for pages containing only one of the following terms',
                '<input type="text" name="xor_terms" size="30">'),
            # TODO: dropdown-box?
            ('Search for pages belonging to one of the following categories',
                '<input type="text" name="categories" size="30">'),
        )
    ])

    search_options = ''.join([
        ''.join([
            f.table_row(1),
            f.table_cell(1, colspan=2),
            f.text(_(txt)),
            f.table_cell(0),
            f.table_row(0),
        ]) for txt in ('Language', 'xxxx')
    ])
    
    html = [
        u'<form method="get" action="">',
        u'<div>',
        u'<input type="hidden" name="action" value="fullsearch">',
        u'<input type="hidden" name="titlesearch" value="%i">' % 0,
        f.table(1),
        search_boxes,
        search_options,
        f.table(0),
        u'<input type="submit" value="%s">' % _('Go get it!'),
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
        

