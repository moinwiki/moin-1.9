# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - email notification plugin from event system

    This code sends email notifications about page changes.
    TODO: refactor it to handle separate events for page changes, creations, etc

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

try:
    set
except:
    from sets import Set as set

from MoinMoin import user
from MoinMoin.Page import Page
from MoinMoin.mail import sendmail
from MoinMoin.events import *
import MoinMoin.events.notification as notification


def send_notification(request, page, comment, emails, email_lang, revisions, trivial):
    """ Send notification email for a single language.

    @param comment: editor's comment given when saving the page
    @param emails: list of email addresses
    @param email_lang: language of email
    @param revisions: revisions of this page (newest first!)
    @param trivial: the change is marked as trivial
    @rtype: int
    @return: sendmail result
    """
    _ = request.getText
    mailBody = notification.page_change_message("page_changed", request, page, email_lang, comment=comment, revisions=revisions)

    return sendmail.sendmail(request, emails,
        _('[%(sitename)s] %(trivial)sUpdate of "%(pagename)s" by %(username)s', formatted=False) % {
            'trivial': (trivial and _("Trivial ", formatted=False)) or "",
            'sitename': page.cfg.sitename or "Wiki",
            'pagename': page.page_name,
            'username': page.uid_override or user.getUserIdentification(request),
        },
        mailBody, mail_from=page.cfg.mail_from)


def notify_subscribers(request, page, comment, trivial):
    """ Send email to all subscribers of given page.

    @param comment: editor's comment given when saving the page
    @param trivial: editor's suggestion that the change is trivial (Subscribers may ignore this)
    @rtype: string
    @return: message, indicating success or errors.
    """
    _ = request.getText
    subscribers = page.getSubscribers(request, return_users=1, trivial=trivial)

    if subscribers:
        recipients = set()

        # get a list of old revisions, and append a diff
        revisions = page.getRevList()

        # send email to all subscribers
        for lang in subscribers:
            emails = [u.email for u in subscribers[lang] if u.notify_by_email]
            names = [u.name for u in subscribers[lang] if u.notify_by_email]
            result = send_notification(request, page, comment, emails, lang, revisions, trivial)
            if result:
                recipients.update(names)

        if recipients:
            return notification.Success(recipients)


def handle(event):
    if isinstance(event, PageChangedEvent) and event.request.cfg.mail_enabled:
        return notify_subscribers(event.request, event.page, event.comment, event.trivial)

