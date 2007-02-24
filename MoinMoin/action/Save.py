# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action macro for saving a page

    MODIFICATION HISTORY:
        @copyright: 2007 by Reimar Bauer 
        @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.Page import Page

def execute(pagename, request):
    if request.user.may.read(pagename):
        thispage = Page(request, pagename)
        thispage.save_raw()


