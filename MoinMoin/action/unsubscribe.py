# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - unsubscribe from notifications to a page.

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.Page import Page

def execute(pagename, request):
    """ Unsubscribe the user from pagename """
    _ = request.getText
    actname = __name__.split('.')[-1]
    if not request.user.valid:
        request.theme.add_msg(_("You must login to use this action: %(action)s.") % {"action": actname}, "error")
        return Page(request, pagename).send_page()

    msg = None

    if request.user.isSubscribedTo([pagename]):
        # Try to unsubscribe
        if request.user.unsubscribe(pagename):
            msg = _('Your subscription to this page has been removed.')
        else:
            msg = _("Can't remove regular expression subscription!") + u' ' + \
                  _("Edit the subscription regular expressions in your settings.")
    else:
        # The user is not subscribed
        msg = _('You need to be subscribed to unsubscribe.')

    Page(request, pagename).send_page(msg=msg)

