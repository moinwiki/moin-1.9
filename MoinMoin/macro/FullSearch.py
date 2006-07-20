# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - FullSearch Macro

    [[FullSearch]]
        displays a search dialog, as it always did.

    [[FullSearch()]]
        does the same as clicking on the page title, only that
        the result is embedded into the page. note the '()' after
        the macro name, which is an empty argument list.

    [[FullSearch(Help)]]
        embeds a search result into a page, as if you entered
        'Help' into the search box.

    The macro creates a page list without context or match info, just
    like PageList macro. It does not make sense to have context in non
    interactive search, and this kind of search is used usually for
    Category pages, where we don't care about the context.

    TODO: If we need to have context for some cases, either we add a
    context argument, or make another macro that use context, which may
    be easier to use.

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re
from MoinMoin import config, wikiutil, search

Dependencies = ["pages"]

def execute(macro, needle):
    request = macro.request
    _ = request.getText

    # if no args given, invoke "classic" behavior
    if needle is None:
        return macro._m_search("fullsearch")

    # With empty arguments, simulate title click (backlinks to page)
    elif needle == '':
        needle = '"%s"' % macro.formatter.page.page_name

    # With whitespace argument, show error message like the one used in the search box
    # TODO: search should implement those errors message for clients
    elif needle.isspace():
        err = _('Please use a more selective search term instead of '
                '{{{"%s"}}}') % needle
        return '<span class="error">%s</span>' % err

    needle = needle.strip()

    # Search the pages and return the results
    results = search.searchPages(request, needle)
    results.sortByPagename()

    return results.pageList(request, macro.formatter, paging=False)


