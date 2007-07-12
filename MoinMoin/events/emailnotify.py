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
from MoinMoin.events import PageChangedEvent, UserCreatedEvent, FileAttachedEvent
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

    subject = _('[%(sitename)s] %(trivial)sUpdate of "%(pagename)s" by %(username)s', formatted=False) % {
            'trivial': (trivial and _("Trivial ", formatted=False)) or "",
            'sitename': page.cfg.sitename or "Wiki",
            'pagename': page.page_name,
            'username': page.uid_override or user.getUserIdentification(request),
        }

    return {'subject': subject, 'body': mailBody}


def send_notification(request, from_address, emails, data):
    """ Send notification email

    @param emails: list of email addresses
    @return: sendmail result
    @rtype int

    """
    return sendmail.sendmail(request, emails, data['subject'], data['body'], mail_from=from_address)


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

    emails = []
    _ = event.request.getText
    user_ids = getUserList(event.request)
    event_name = event.__class__.__name__

    from_address = event.request.cfg.mail_from
    email = event.user.email or u"NOT SET"
    sitename = event.request.cfg.sitename
    username = event.user.name

    data = notification.user_created_message(event.request, sitename, username, email)

    for id in user_ids:
        usr = User(event.request, id=id)
        if not usr.notify_by_email:
            continue

        # Currently send this only to super users
        if usr.isSuperUser() and event_name in usr.subscribed_events and usr.notify_by_email:
            emails.append(usr.email)

    send_notification(event.request, from_address, emails, data)


def handle_file_attached(event):
    """Sends an email to super users that have subscribed to this event type"""

    names = set()
    _ = event.request.getText
    event_name = event.__class__.__name__
    from_address = event.request.cfg.mail_from
    request = event.request
    page = Page(request, event.pagename)

    subscribers = page.getSubscribers(request, return_users=1)
    notification.filter_subscriber_list(event, subscribers, False)
    data = notification.attachment_added(request, event.pagename, event.name, event.size)

    for lang in subscribers:
        emails = []

        for usr in subscribers[lang]:
            if usr.notify_by_email and event_name in usr.subscribed_events:
                emails.append(usr.email)
            else:
                continue

            if send_notification(request, from_address, emails, data):
                names.update(usr.name)

    return notification.Success(names)


def handle(event):
    """An event handler"""

    if not event.request.cfg.mail_enabled:
        return

    if isinstance(event, PageChangedEvent):
        return notify_subscribers(event.request, event.page, event.comment, event.trivial)
    elif isinstance(event, UserCreatedEvent):
        return handle_user_created(event)
    elif isinstance(event, FileAttachedEvent):
        return handle_file_attached(event)
