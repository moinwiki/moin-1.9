# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Configuration Help
"""
from MoinMoin.config import multiconfig

Dependencies = ['']
generates_headings = True

def macro_WikiConfigHelp(macro):
    request = macro.request
    _ = request.getText
    f = macro.request.formatter
    ret = []

    groups = []
    for groupname in multiconfig.options:
        groups.append((groupname, True, multiconfig.options))
    for groupname in multiconfig.options_no_group_name:
        groups.append((groupname, False, multiconfig.options_no_group_name))
    groups.sort()

    for groupname, addgroup, optsdict in groups:
        desc, opts = optsdict[groupname]
        ret.extend([
            f.heading(1, 1),
            ## XXX: translate description?
            f.text(desc),
            f.heading(0, 1),
            f.table(1),
            f.table_row(1),
            f.table_cell(1), f.strong(1), f.text(_('Variable name')), f.strong(0), f.table_cell(0),
            f.table_cell(1), f.strong(1), f.text(_('Default')), f.strong(0), f.table_cell(0),
            f.table_cell(1), f.strong(1), f.text(_('Description')), f.strong(0), f.table_cell(0),
            f.table_row(0),
        ])
        opts = list(opts)
        opts.sort()
        for name, default, description in opts:
            if addgroup:
                name = groupname + '_' + name
            default_txt = '%r' % (default, )
            if len(default_txt) > 50:
                default_txt = '...'
            ret.extend([
                f.table_row(1),
                f.table_cell(1), f.text(name), f.table_cell(0),
                f.table_cell(1), f.code(1, css="backtick"), f.text(default_txt), f.code(0), f.table_cell(0),
                ## XXX: translate description?
                f.table_cell(1), f.text(description or 'No description provided'), f.table_cell(0),
                f.table_row(0),
            ])
        ret.append(f.table(0))

    return ''.join(ret)
