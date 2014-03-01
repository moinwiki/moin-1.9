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
from MoinMoin.PageEditor import PageEditor
from MoinMoin.user import User

def test_get_handlers(request):
    """Test if there are any event handlers. There should be some internal ones"""

    assert events.get_handlers(request.cfg)

def test_send_event(request):
    """Test if event handlers are called and if proper messages are returned"""

    py.test.skip('broken test - global state is changed somehow that test_GetVal looks broken')
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
    page = PageEditor(request, "FrontPage")

    print "Provided with a dumb change type argument, this should raise an exception!"
    py.test.raises(notification.UnknownChangeType, notification.page_change_message,
                   "StupidType", request, page, "en", revisions=page.getRevList())

def test_user_created_event(request):
    py.test.skip("Test is wrong, because it assumes send_notification will be called - but if there is no superuser subscribed to UserCreatedEvent, then no notification needs to be sent.")
    class server_dummy:
        def __init__(self):
            self.sent = False

        def send_notification(self, *args):
            self.sent = True

    event = events.UserCreatedEvent(request, User(request))
    request.cfg.notification_server = server_dummy()
    request.cfg.secrets = "thisisnotsecret"

    jabbernotify.handle_user_created(event)
    assert request.cfg.notification_server.sent is True

def test_filter_subscriber_list(request):
    user = User(request)
    event = events.Event(request)

    print "User is subscribed to this event on jabber."
    print "This means, that he should stay on the list."
    user.jid = "user@example.com"
    user.jabber_subscribed_events = [events.Event.__name__]
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, True)
    assert subscribers["en"]

    print "User is not subscribed to this event on jabber."
    print "The list should be empty."
    user.jid = "user@example.com"
    user.jabber_subscribed_events = []
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, True)
    assert not subscribers["en"]

    print "User is subscribed to this event on email."
    print "This means, that he should stay on the list."
    user.email = "user@example.com"
    user.email_subscribed_events = [events.Event.__name__]
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, False)
    assert subscribers["en"]

    print "User is not subscribed to this event on email."
    print "The list should be empty."
    user.email = "user@example.com"
    user.email_subscribed_events = []
    subscribers = {"en": [user]}
    notification.filter_subscriber_list(event, subscribers, False)
    assert not subscribers["en"]

coverage_modules = ["MoinMoin.events"]
