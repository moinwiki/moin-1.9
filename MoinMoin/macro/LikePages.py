# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create list of LikePages

    @copyright: 2004 by Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = ['namespace']

from MoinMoin.action import LikePages

def execute(macro, args):
    request = macro.request
    pagename = macro.formatter.page.page_name
    
    # Get matches
    start, end, matches = LikePages.findMatches(pagename, request)

    # Render matches
    if matches and not isinstance(matches, (str, unicode)):
        import StringIO
        out = StringIO.StringIO()
        request.redirect(out)
        LikePages.showMatches(pagename, request, start, end, matches, False)
        request.redirect()
        return out.getvalue()
    return args
