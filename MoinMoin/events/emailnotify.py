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
from MoinMoin.events import PageChangedEvent, UserCreatedEvent
from MoinMoin.user import User, getUserList
import MoinMoin.events.notification as notification


def prep_page_changed_mail(request, page, comment, email_lang, revisions, trivial):
    """ Prepare information required for email notification about page change

    @param page: the modified page instance
    @param comment: editor's comment given when saving the page
    @param email_lang: language of email
    @param revisions: revisions of this page (newest first!)
    @param trivial: the change is marked as trivial
    @return: dict with email title and body
    @rtype: dict

    """
    _ = request.getText
    mailBody = notification.page_change_message("page_changed", request, page, email_lang, comment=comment, revisions=revisions)

    title = _('[%(sitename)s] %(trivial)sUpdate of "%(pagename)s" by %(username)s', formatted=False) % {
            'trivial': (trivial and _("Trivial ", formatted=False)) or "",
            'sitename': page.cfg.sitename or "Wiki",
            'pagename': page.page_name,
            'username': page.uid_override or user.getUserIdentification(request),
        }

    return {'title': title, 'body': mailBody}


def send_notification(request, from_address, emails, data):
    """ Send notification email

    @param emails: list of email addresses
    @return: sendmail result
    @rtype int

    """
    return sendmail.sendmail(request, emails, data['title'], data['body'], mail_from=from_address)


def notify_subscribers(request, page, comment, trivial):
    """ Send email to all subscribers of given page.

    @param comment: editor's comment given when saving the page
    @param trivial: editor's suggestion that the change is trivial (Subscribers may ignore this)
    @rtype: string
    @return: message, indicating success or errors.

    """
    _ = request.getText
    subscribers = page.getSubscribers(request, return_users=1, trivial=trivial)
    mail_from = page.cfg.mail_from

    if subscribers:
        recipients = set()

        # get a list of old revisions, and append a diff
        revisions = page.getRevList()

        # send email to all subscribers
        for lang in subscribers:
            emails = [u.email for u in subscribers[lang] if u.notify_by_email]
            names = [u.name for u in subscribers[lang] if u.notify_by_email]
            data = prep_page_changed_mail(request, page, comment, lang, revisions, trivial)

            if send_notification(request, mail_from, emails, data):
                recipients.update(names)

        if recipients:
            return notification.Success(recipients)


def handle_user_created(event):
    """Sends an email to super users that have subscribed to this event type"""

    user_ids = getUserList(event.request)
    emails = []
    event_name = event.__class__.__name__
    email = event.user.email or u"NOT SET"
    _ = event.request.getText

    title = _("New user account created on %(sitename)s")
    body = _("""Dear Superuser, a new user has just been created. Details follow:
    User name: %s
    Email address: %s)""")

    data = {'from': event.request.cfg.mail_from, 'title': title, 'body': body}
    emails = []

    for id in user_ids:
        usr = User(event.request, id=id)
        if not usr.notify_by_email:
            continue

        # Currently send this only to super users
        if usr.isSuperUser() and event_name in usr.subscribed_events:
            emails.append(usr.email)

    send_notification(event.request, emails, data)

def handle(event):
    """An event handler"""

    if not event.request.cfg.mail_enabled:
        return

    if isinstance(event, PageChangedEvent):
        return notify_subscribers(event.request, event.page, event.comment, event.trivial)
    elif isinstance(event, UserCreatedEvent):
        return handle_user_created(event)

