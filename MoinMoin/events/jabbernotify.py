# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber notification plugin for event system

    This code sends notifications using a separate daemon.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import xmlrpclib

from MoinMoin.user import User, getUserList
from MoinMoin.Page import Page

import MoinMoin.events as ev
from MoinMoin.events.messages import page_change_message

# XML RPC Server object used to communicate with notification bot
server = None


def handle(event):
    global server

    cfg = event.request.cfg

    # Check for desired event type and if notification bot is configured
    if not cfg.jabber_enabled:
        return
    
    # Create an XML RPC server object only if it doesn't exist
    if server is None:
        server = xmlrpclib.Server("http://" + cfg.bot_host)
    
    if isinstance(event, ev.PageChangedEvent):
        return handle_page_changed(event)
    elif isinstance(event, ev.JabberIDSetEvent) or isinstance(event, ev.JabberIDUnsetEvent):
        return handle_jid_changed(event)
    elif isinstance(event, ev.FileAttachedEvent):
        return handle_file_attached(event)
    elif isinstance(event, ev.PageDeletedEvent):
        return handle_page_deleted(event)
    

def handle_jid_changed(event):
    """ Handles events sent when user's JID changes """
    
    request = event.request
    _ = request.getText
    
    try:
        if isinstance(event, JabberIDSetEvent):
            server.addJIDToRoster(request.cfg.secret, event.jid)
        else:
            server.removeJIDFromRoster(request.cfg.secret, event.jid)        
                
    except xmlrpclib.Error, err:
        print _("XML RPC error: "), str(err)
        return (0, _("Notifications not sent"))
    except Exception, err:
        print _("Low-level communication error: "), str(err)
        return (0, _("Notifications not sent"))


def handle_file_attached(event):
    """Handles event sent when a file is attached to a page"""
    
    request = event.request
    page = Page(request, event.pagename) 
    
    subscribers = page.getSubscribers(request, return_users=1)
    page_change("attachment_added", request, page, subscribers, attach_name=event.attachment_name, attach_size=event.size)

        
def handle_page_changed(event):
    """ Handles events related to page changes """
    
    request = event.request
    page = event.page
    
    subscribers = page.getSubscribers(request, return_users=1, trivial=event.trivial)
    page_change("page_changed", request, page, subscribers, revisions=page.getRevList(), comment=event.comment)
    

def handle_page_deleted(event):
    """Handles event sent when a page is deleted"""
    
    request = event.request
    page = event.page
    
    subscribers = page.getSubscribers(request, return_users=1)
    page_change("page_deleted", request, page, subscribers)
    

def page_change(type, request, page, subscribers, **kwargs):
    
    _ = request.getText
    
    if subscribers:
        # send notifications to all subscribers
        results = [_('Status of sending notifications:')]
        for lang in subscribers:
            jids = [u.jid for u in subscribers[lang]]
            names = [u.name for u in subscribers[lang]]
            msg = page_change_message(type, request, page, lang, **kwargs)
            jabberok, status = send_notification(request, jids, msg)
            recipients = ", ".join(names)
            results.append(_('[%(lang)s] %(recipients)s: %(status)s') % {
                'lang': lang, 'recipients': recipients, 'status': status})

        # Return notifications sent results. Ignore trivial - we don't have
        # to lie. If notification was sent, just tell about it.
        return '<p>\n%s\n</p> ' % '<br>'.join(results)

    # No notifications sent, no message.
    return ''

def send_notification(request, jids, message):
    """ Send notifications for a single language.

    @param comment: editor's comment given when saving the page
    @param jids: list of Jabber IDs
    @param message_lang: language of notification
    @param revisions: revisions of this page (newest first!)
    @param trivial: the change is marked as trivial
    """
    _ = request.getText
    
    for jid in jids:
        # FIXME: stops sending notifications on first error
        try:
            server.send_notification(request.cfg.secret, jid, message)
        except xmlrpclib.Error, err:
            print _("XML RPC error: "), str(err)
            return (0, _("Notifications not sent"))
        except Exception, err:
            print _("Low-level communication error: "), str(err)
            return (0, _("Notifications not sent"))
        
    return (1, _("Notifications sent OK"))
