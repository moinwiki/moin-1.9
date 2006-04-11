# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - OrphanedPages Macro

    @copyright: 2001 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = ["pages"]

def execute(macro, args):
    _ = macro.request.getText

    if macro.request.mode_getpagelinks: # prevent recursion
        return ''
    
    # delete all linked pages from a dict of all pages
    pages = macro.request.rootpage.getPageDict()
    orphaned = {}
    orphaned.update(pages)
    for page in pages.values():
        links = page.getPageLinks(macro.request)
        for link in links:
            if link in orphaned:
                del orphaned[link]

    # check for the extreme case
    if not orphaned:
        return "<p>%s</p>" % _("No orphaned pages in this wiki.")

    # return a list of page links
    orphanednames = orphaned.keys()
    orphanednames.sort()
    result = []
    result.append(macro.formatter.number_list(1))
    for name in orphanednames:
        if not name: continue
        result.append(macro.formatter.listitem(1))
        result.append(macro.formatter.pagelink(1, name, generated=1))
        result.append(macro.formatter.text(name))
        result.append(macro.formatter.pagelink(0, name))
        result.append(macro.formatter.listitem(0))
    result.append(macro.formatter.number_list(0))

    return ''.join(result)

