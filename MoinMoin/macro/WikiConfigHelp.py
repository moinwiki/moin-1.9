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
            f.text(desc),
            f.heading(0, 1),
            f.definition_list(1),
        ])
        opts = list(opts)
        opts.sort()
        for name, default, description in opts:
            if addgroup:
                name = groupname + '_' + name
            ret.extend([
                f.definition_term(1),
                f.text(name),
                f.definition_term(0),
                f.definition_desc(1),
                f.text(description or u'No help available'),
                f.definition_desc(0),
            ])
        ret.append(f.definition_list(0))

    return ''.join(ret)
