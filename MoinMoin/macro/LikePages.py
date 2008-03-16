# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create list of LikePages

    @copyright: 2004 Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = ['namespace']

from MoinMoin.action import LikePages

def macro_LikePages(macro):
    request = macro.request
    # we don't want to spend much CPU for spiders requesting nonexisting pages
    if not request.isSpiderAgent:
        pagename = macro.formatter.page.page_name

        # Get matches
        start, end, matches = LikePages.findMatches(pagename, request)

        # Render matches
        if matches and not isinstance(matches, (str, unicode)):
            return request.redirectedOutput(LikePages.showMatches, pagename, request, start, end, matches, False)

    return ''

