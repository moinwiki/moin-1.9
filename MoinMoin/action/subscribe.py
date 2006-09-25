# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - subscribe to a page to get notified when it changes

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.Page import Page

def execute(pagename, request):
    """ Subscribe or unsubscribe the user to pagename
    
    TODO: what if subscribe failed? no message is displayed.
    """
    _ = request.getText
    cfg = request.cfg
    msg = None

    if not request.user.may.read(pagename):
        msg = _("You are not allowed to subscribe to a page you can't read.")

    # Check if mail is enabled
    elif not cfg.mail_enabled:
        msg = _("This wiki is not enabled for mail processing.")

    # Suggest visitors to login
    elif not request.user.valid:
        msg = _("You must log in to use subscribtions.")

    # Suggest users without email to add their email address
    elif not request.user.email:
        msg = _("Add your email address in your UserPreferences to use subscriptions.")

    elif request.user.isSubscribedTo([pagename]):
        # Try to unsubscribe
        if request.user.unsubscribe(pagename):
            msg = _('Your subscribtion to this page has been removed.')
        else:
            msg = _("Can't remove regular expression subscription!") + u' ' + \
                  _("Edit the subscription regular expressions in your "
                    "UserPreferences.")

    else:
        # Try to subscribe
        if request.user.subscribe(pagename):
            msg = _('You have been subscribed to this page.')

    Page(request, pagename).send_page(request, msg=msg)

