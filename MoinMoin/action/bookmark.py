# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - set or delete bookmarks (in time) for RecentChanges

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import time

from MoinMoin import wikiutil
from MoinMoin.Page import Page

def execute(pagename, request):
    """ set bookmarks (in time) for RecentChanges or delete them """
    timestamp = request.form.get('time', [None])[0]
    if timestamp is not None:
        if timestamp == 'del':
            tm = None
        else:
            try:
                tm = int(timestamp)
            except StandardError:
                tm = wikiutil.timestamp2version(time.time())
    else:
        tm = wikiutil.timestamp2version(time.time())

    if tm is None:
        request.user.delBookmark()
    else:
        request.user.setBookmark(tm)
    request.page.send_page(request)

