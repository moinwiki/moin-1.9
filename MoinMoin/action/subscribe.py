# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - subscribe to a page to get notified when it changes

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.Page import Page

def execute(pagename, request):
    """ Subscribe or unsubscribe the user to pagename """
    _ = request.getText
    cfg = request.cfg
    msg = None

    if not request.user.may.read(pagename):
        msg = _("You are not allowed to subscribe to a page you can't read.")

    # Check if mail is enabled
    elif not cfg.mail_enabled and not cfg.jabber_enabled
        msg = _("This wiki is not enabled for mail/Jabber processing.")

    # Suggest visitors to login
    elif not request.user.valid:
        msg = _("You must log in to use subscriptions.")

    # Suggest users without email to add their email address
    elif not request.user.email and not request.user.jid:
        msg = _("Add your email address or Jabber ID in your UserPreferences to use subscriptions.")

    elif request.user.isSubscribedTo([pagename]):
        # Try to unsubscribe
        if request.user.unsubscribe(pagename):
            msg = _('Your subscription to this page has been removed.')
        else:
            msg = _("Can't remove regular expression subscription!") + u' ' + \
                  _("Edit the subscription regular expressions in your "
                    "UserPreferences.")

    else:
        # Try to subscribe
        if request.user.subscribe(pagename):
            msg = _('You have been subscribed to this page.')
        else: # should not happen
            msg = _('You could not get subscribed to this page.')

    Page(request, pagename).send_page(msg=msg)

