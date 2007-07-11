# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests for MoinMoin.events module

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import py

import MoinMoin.events as events
import MoinMoin.events.notification as notification
import MoinMoin.events.jabbernotify as jabbernotify
from MoinMoin.Page import Page
from MoinMoin.user import User

def test_get_handlers(request):
    """Test if there are any event handlers. There should be some internal ones"""

    assert events.get_handlers(request.cfg)

def test_send_event(request):
    """Test if event handlers are called and if proper messages are returned"""

    return_string = u"test_send_event"

    def event_handler(event):
        return notification.Failure("Just a test")

    request.cfg.event_handlers = [event_handler]
    event = events.Event(request)

    print "A proper event handler must be called and an 1-element list of results returned"
    results = events.send_event(event)
    assert issubclass(results[0].__class__, events.EventResult)

def test_subscribable_events(request):
    """Test if there are any subscribable events. There should be some."""

    print "There should be at least a few subscribable events!"
    assert events.get_subscribable_events()

def test_page_change_message(request):
    page = Page(request, "FrontPage")

    print "Provided with a dumb change type argument, this should raise an exception!"
    py.test.raises(notification.UnknownChangeType, notification.page_change_message,
                   "StupidType", request, page, "en", revisions=page.getRevList())

def test_filter_subscriber_list(request):
    user = User(request)
    event = events.Event(request)

    print "User is subscribed to this event and wants to get notified by jabber."
    print "This means, that he should stay on the list."
    user.notify_by_jabber = True
    user.jid = "user@example.com"
    user.subscribed_events = [events.Event.__name__]
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, True)
    assert subscribers["en"]

    print "User is subscribed to this event, but doesn't want to get notified by jabber."
    print "The list should be empty."
    user.notify_by_jabber = False
    user.jid = "user@example.com"
    user.subscribed_events = [events.Event.__name__]
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, True)
    assert not subscribers["en"]

    print "User is not subscribed to this event, but wants to get notfied by jabber."
    print "The list should be empty."
    user.notify_by_jabber = True
    user.jid = "user@example.com"
    user.subscribed_events = []
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, True)
    assert not subscribers["en"]

    print "User is neither subscribed to this event, nor wants jabber notifications."
    print "The list should be empty."
    user.notify_by_jabber = False
    user.subscribed_events = []
    user.jid = "user@example.com"
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, True)
    assert not subscribers["en"]

coverage_modules = ["MoinMoin.events"]
