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
    msg = None

    if not request.user.valid:
        msg = _("You must login to add a quicklink.")
    elif request.user.isQuickLinkedTo([pagename]):
        if request.user.removeQuicklink(pagename):
            msg = _('Your quicklink to this page has been removed.')
        else: # should not happen
            msg = _('Your quicklink to this page could not be removed.')
    else:
        if request.user.addQuicklink(pagename):
            msg = _('A quicklink to this page has been added for you.')
        else: # should not happen
            msg = _('A quicklink to this page could not be added for you.')

    Page(request, pagename).send_page(msg=msg)

