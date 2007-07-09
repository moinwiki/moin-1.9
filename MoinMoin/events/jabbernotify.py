# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber notification plugin for event system

    This code sends notifications using a separate daemon.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import xmlrpclib

try:
    set
except:
    from sets import Set as set

from MoinMoin import error
from MoinMoin.Page import Page
from MoinMoin.user import User, getUserList
import MoinMoin.events.notification as notification
import MoinMoin.events as ev


def handle(event):
    """An event handler"""

    cfg = event.request.cfg

    # Check for desired event type and if notification bot is configured
    if not cfg.jabber_enabled:
        return

    if isinstance(event, ev.PageChangedEvent):
        return handle_page_changed(event)
    elif isinstance(event, ev.JabberIDSetEvent) or isinstance(event, ev.JabberIDUnsetEvent):
        return handle_jid_changed(event)
    elif isinstance(event, ev.FileAttachedEvent):
        return handle_file_attached(event)
    elif isinstance(event, ev.PageDeletedEvent):
        return handle_page_deleted(event)
    elif isinstance(event, ev.PageRenamedEvent):
        return handle_page_renamed(event)
    elif isinstance(event, ev.UserCreatedEvent):
        return handle_user_created(event)


def handle_jid_changed(event):
    """ Handles events sent when user's JID changes """

    request = event.request
    server = request.cfg.notification_server
    _ = request.getText

    try:
        if isinstance(event, ev.JabberIDSetEvent):
            server.addJIDToRoster(request.cfg.secret, event.jid)
        else:
            server.removeJIDFromRoster(request.cfg.secret, event.jid)

    except xmlrpclib.Error, err:
        ev.logger.error(_("XML RPC error: %s"), str(err))
    except Exception, err:
        ev.logger.error(_("Low-level communication error: $s"), str(err))


def _filter_subscriber_list(event, subscribers):
    """Filter a list of page subscribers to honor event subscriptions

    @param subscribers: list of subscribers (dict of lists, language is the key)
    @type subscribers: dict

    """
    event_name = event.__class__.__name__

    # Filter the list by removing users who don't want to receive
    # notifications about this type of event
    for lang in subscribers.keys():
        userlist = []

        for usr in subscribers[lang]:
            if event_name in usr.subscribed_events and usr.notify_by_jabber:
                userlist.append(usr)

        subscribers[lang] = userlist

def handle_file_attached(event):
    """Handles event sent when a file is attached to a page"""

    request = event.request
    page = Page(request, event.pagename)

    subscribers = page.getSubscribers(request, return_users=1)
    _filter_subscriber_list(event, subscribers)

    return page_change("attachment_added", request, page, subscribers, \
                       attach_name=event.attachment_name, attach_size=event.size)


def handle_page_changed(event):
    """ Handles events related to page changes """
    request = event.request
    page = event.page

    subscribers = page.getSubscribers(request, return_users=1, trivial=event.trivial)
    _filter_subscriber_list(event, subscribers)
    return page_change("page_changed", request, page, subscribers, \
                       revisions=page.getRevList(), comment=event.comment)


def handle_page_deleted(event):
    """Handles event sent when a page is deleted"""

    request = event.request
    page = event.page

    subscribers = page.getSubscribers(request, return_users=1)
    _filter_subscriber_list(event, subscribers)
    return page_change("page_deleted", request, page, subscribers)

def handle_page_renamed(event):
    """Handles event sent when a page is renamed"""

    request = event.request
    page = event.page
    old_name = event.old_page.page_name

    subscribers = page.getSubscribers(request, return_users=1)
    _filter_subscriber_list(event, subscribers)
    return page_change("page_renamed", request, page, subscribers, oldname=old.page_name)


def handle_user_created(event):
    """Handles an event sent when a new user is being created"""

    jids = []
    user_ids = getUserList(event.request)
    event_name = event.__class__.__name__
    email = event.user.email or u"NOT SET"
    msg = u"""Dear Superuser, a new user has just been created. Details follow:
    User name: %s
    Email address: %s
    """

    email = event.user.email or u"NOT SET"

    for id in user_ids:
        usr = User(event.request, id=id)
        if not usr.notify_by_jabber:
            continue

        # Currently send this only to super users
        if usr.isSuperUser() and usr.jid and event_name in usr.subscribed_events:
            jids.append(usr.jid)

    send_notification(event.request, jids, msg % (event.user.name, email))


def page_change(type, request, page, subscribers, **kwargs):
    """Sends notification about page being changed in some way"""
    _ = request.getText

    # send notifications to all subscribers
    if subscribers:
        recipients = set()

        for lang in subscribers:
            jids = [u.jid for u in subscribers[lang] if u.jid]
            names = [u.name for u in subscribers[lang] if u.jid]
            msg = notification.page_change_message(type, request, page, lang, **kwargs)
            result = send_notification(request, jids, msg)

            if result:
                recipients.update(names)

        if recipients:
            return notification.Success(recipients)

def send_notification(request, jids, message):
    """ Send notifications for a single language.

    @param comment: editor's comment given when saving the page
    @param jids: an iterable of Jabber IDs to send the message to
    """
    _ = request.getText
    server = request.cfg.notification_server

    try:
        server.send_notification(request.cfg.secret, jids, message)
        return True
    except xmlrpclib.Error, err:
        ev.logger.error(_("XML RPC error: %s"), str(err))
    except Exception, err:
        ev.logger.error(_("Low-level communication error: %s"), str(err), )

