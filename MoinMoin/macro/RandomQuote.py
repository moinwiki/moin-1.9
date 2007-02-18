# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RandomQuote Macro

    Selects a random quote from FortuneCookies or a given page.

    Usage:
        [[RandomQuote()]]
        [[RandomQuote(WikiTips)]]
    
    Comments:
        It will look for list delimiters on the page in question.
        It will ignore anything that is not in an "*" list.

    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
    
    Originally written by Thomas Waldmann.
    Gustavo Niemeyer added wiki markup parsing of the quotes.
"""

import random, StringIO
from MoinMoin.Page import Page, wikiutil

Dependencies = ["time"]

def execute(macro, args):
    _ = macro.request.getText

    pagename = args or 'FortuneCookies'
    if macro.request.user.may.read(pagename):
        page = Page(macro.request, pagename)
        raw = page.get_raw_body()
    else:
        raw = ""

    # this selects lines looking like a list item
    # !!! TODO: make multi-line quotes possible (optionally split by "----" or something)
    quotes = raw.splitlines()
    quotes = [quote.strip() for quote in quotes]
    quotes = [quote[2:] for quote in quotes if quote.startswith('* ')]

    if not quotes:
        return (macro.formatter.highlight(1) +
                _('No quotes on %(pagename)s.') % {'pagename': pagename} +
                macro.formatter.highlight(0))

    quote = random.choice(quotes)
    page.set_raw_body(quote, 1)
    quote = macro.request.redirectedOutput(page.send_page,
        content_only=1, content_id="RandomQuote_%s" % wikiutil.quoteWikinameFS(page.page_name) )

    return quote

