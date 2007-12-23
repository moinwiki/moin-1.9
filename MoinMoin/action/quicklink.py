# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - add a quicklink to the user's quicklinks

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.Page import Page

def execute(pagename, request):
    """ Add the current wiki page to the user quicklinks """
    _ = request.getText

    if not request.user.valid:
        request.theme.add_msg(_("You must login to add a quicklink."), "error")
    elif request.user.isQuickLinkedTo([pagename]):
        if request.user.removeQuicklink(pagename):
            request.theme.add_msg(_('Your quicklink to this page has been removed.'), "info")
        else: # should not happen
            request.theme.add_msg(_('Your quicklink to this page could not be removed.'), "error")
    else:
        if request.user.addQuicklink(pagename):
            request.theme.add_msg(_('A quicklink to this page has been added for you.'), "info")
        else: # should not happen
            request.theme.add_msg(_('A quicklink to this page could not be added for you.'), "error")

    Page(request, pagename).send_page()

