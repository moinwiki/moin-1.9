# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RandomPage Macro

    @copyright: 2000 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import random
random.seed()

from MoinMoin.Page import Page

Dependencies = ["time"]

def execute(macro, args):
    request = macro.request

    # get number of wanted links        
    try:
        links = max(int(args), 1)
    except StandardError:
        links = 1

    # Get full page unfiltered page list - very fast!
    all_pages = request.rootpage.getPageList(user='', exists=0)

    # Now select random page from the full list, and if it exists and we
    # can read it, save.
    pages = []
    found = 0
    while found < links and all_pages:
        # Take one random page from the list
        pagename = random.choice(all_pages)
        all_pages.remove(pagename)

        # Filter out deleted pages or pages the user may not read.
        page = Page(request, pagename)
        if page.exists() and request.user.may.read(pagename):
            pages.append(pagename)
            found += 1

    if not pages:
        return ''

    f = macro.formatter

    # return a single page link
    if links == 1:
        name = pages[0]
        return (f.pagelink(1, name, generated=1) +
                f.text(name) +
                f.pagelink(0, name))

    # return a list of page links
    pages.sort()
    result = []
    write = result.append

    write(f.bullet_list(1))
    for name in pages:
        write(f.listitem(1))
        write(f.pagelink(1, name, generated=1))
        write(f.text(name))
        write(f.pagelink(0, name))
        write(f.listitem(0))
    write(f.bullet_list(0))

    result = ''.join(result)
    return result


