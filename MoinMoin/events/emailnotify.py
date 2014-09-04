# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - email notification plugin from event system

    This code sends email notifications about page changes.
    TODO: refactor it to handle separate events for page changes, creations, etc

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user
from MoinMoin.Page import Page
from MoinMoin.mail import sendmail
from MoinMoin.support.python_compatibility import set
from MoinMoin.user import User, superusers
from MoinMoin.action.AttachFile import getAttachUrl

import MoinMoin.events as ev
import MoinMoin.events.notification as notification


def prep_page_changed_mail(request, page, comment, email_lang, revisions,
                           trivial=False, change_type="page_changed",
                           old_page=None):
    """ Prepare information required for email notification about page change

    @param page: the modified page instance
    @param comment: editor's comment given when saving the page
    @param email_lang: language of email
    @param revisions: revisions of this page (newest first!)
    @param trivial: the change is marked as trivial
    @return: dict with email title and body
    @rtype: dict

    """
    old_name = old_page and old_page.page_name or None  # for rename
    change = notification.page_change_message(change_type, request, page, email_lang,
                                              comment=comment, revisions=revisions, trivial=trivial,
                                              old_name=old_name)
    _ = lambda text: request.getText(text, lang=email_lang)
    cfg = request.cfg
    intro = change['text']
    diff = change['diff']
    subject = change['subject']

    if change.has_key('comment'):
        comment = _("Comment:") + "\n" + change['comment'] + "\n\n"
    else:
        comment = ''

    diff_revs = None
    if change_type == "page_changed" and len(revisions) >= 2:
        diff_revs = revisions[1], revisions[0]
    elif change_type == "page_deleted" and len(revisions) >= 1:
        diff_revs = revisions[0], revisions[0] + 1

    if diff_revs:
        querystr = {'action': 'diff', 'rev1': str(diff_revs[0]), 'rev2': str(diff_revs[1])}
    else:
        querystr = {}

    # links to diff or to page (if only 1 rev):
    difflink = request.getQualifiedURL(page.url(request, querystr))
    # always links to page:
    pagelink = request.getQualifiedURL(page.url(request))

    sitename = page.cfg.sitename or "Wiki"
    pagename = page.page_name
    username = page.uid_override or user.getUserIdentification(request)

    text = _(cfg.mail_notify_page_text) % locals()
    return {'subject': subject, 'text': text}


def send_notification(request, from_address, emails, data):
    """ Send notification email

    @param emails: list of email addresses
    @return: sendmail result
    @rtype int

    """
    return sendmail.sendmail(request, emails, data['subject'], data['text'], mail_from=from_address)


def handle_page_changed(event):
    """ Send email to all subscribers of given page.

    @param event: event to notify about
    @rtype: string
    @return: message, indicating success or errors.

    """
    comment = event.comment
    page = event.page
    request = event.request
    trivial = isinstance(event, ev.TrivialPageChangedEvent)
    old_page = None
    if isinstance(event, (ev.PageChangedEvent, ev.TrivialPageChangedEvent)):
        change_type = "page_changed"
    elif isinstance(event, ev.PageDeletedEvent):
        change_type = "page_deleted"
    elif isinstance(event, ev.PageRenamedEvent):
        change_type = "page_renamed"
        old_page = event.old_page
    subscribers = page.getSubscribers(request, return_users=1)
    mail_from = page.cfg.mail_from

    if subscribers:
        recipients = set()

        # get a list of old revisions, and append a diff
        revisions = page.getRevList()

        # send email to all subscribers
        for lang in subscribers:
            users = [u for u in subscribers[lang]
                     if event.name in u.email_subscribed_events]
            emails = [u.email for u in users]
            names = [u.name for u in users]
            data = prep_page_changed_mail(request, page, comment, lang, revisions,
                                          trivial=trivial, change_type=change_type,
                                          old_page=old_page)

            if send_notification(request, mail_from, emails, data):
                recipients.update(names)

        if recipients:
            return notification.Success(recipients)


def handle_file_changed(event):
    """Sends an email to users that have subscribed to this event type"""

    names = set()
    from_address = event.request.cfg.mail_from
    request = event.request
    page = Page(request, event.pagename)

    if isinstance(event, ev.FileAttachedEvent):
        notification_fn = notification.attachment_added
    elif isinstance(event, ev.FileRemovedEvent):
        notification_fn = notification.attachment_removed

    subscribers = page.getSubscribers(request, return_users=1)
    notification.filter_subscriber_list(event, subscribers, False)
    recipients = []

    for lang in subscribers:
        recipients.extend(subscribers[lang])

    attachlink = request.getQualifiedURL(getAttachUrl(event.pagename, event.filename, request))
    pagelink = request.getQualifiedURL(page.url(request, {}))

    for lang in subscribers:
        _ = lambda text: request.getText(text, lang=lang)

        links = _("Attachment link: %(attach)s\n" \
                  "Page link: %(page)s\n") % {'attach': attachlink, 'page': pagelink}

        data = notification_fn(request, _, event.pagename, event.filename, event.size)
        data['text'] = data['text'] + links

        emails = [usr.email for usr in subscribers[lang]]

        if send_notification(request, from_address, emails, data):
            names.update(recipients)

    return notification.Success(names)


def handle_user_created(event):
    """Sends an email to super users that have subscribed to this event type"""

    request = event.request
    sitename = request.cfg.sitename
    from_address = request.cfg.mail_from
    event_name = event.name
    email = event.user.email or u"NOT SET"
    username = event.user.name

    for usr in superusers(request):
        if usr.email and event_name in usr.email_subscribed_events:
            _ = lambda text: request.getText(text, lang=usr.language or 'en')
            data = notification.user_created_message(request, _, sitename, username, email)
            send_notification(request, from_address, [usr.email], data)


def handle(event):
    """An event handler"""

    if not event.request.cfg.mail_enabled:
        return

    if isinstance(event, (ev.PageChangedEvent, ev.TrivialPageChangedEvent,
                          ev.PageDeletedEvent, ev.PageRenamedEvent)):
        return handle_page_changed(event)
    elif isinstance(event, (ev.FileAttachedEvent, ev.FileRemovedEvent)):
        return handle_file_changed(event)
    elif isinstance(event, ev.UserCreatedEvent):
        return handle_user_created(event)
