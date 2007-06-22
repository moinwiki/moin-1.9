# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests for MoinMoin.events module

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.request.CLI import Request
import MoinMoin.events as events

def test_get_handlers(request):
    """Test if there are any event handlers. There should be some internal ones"""
    
    assert events.get_handlers(request.cfg)

def test_send_event(request):
    """Test if event handlers are called and if proper messages are returned"""
    
    return_string = u"test_send_event"
    
    def event_handler(event):
        return return_string
    
    request.cfg.event_handlers = [event_handler]
    event = events.Event(request)
    
    print "A proper event handler should be called, and an 1-element list of messages returned"
    assert events.send_event(event)[0] == return_string

def test_subscribable_events(request):
    """Test if there are any subscribable events. There should be some."""
    
    print "There should be at least a few subscribable events!"
    assert events.get_subscribable_events()
    
coverage_modules = ["MoinMoin.events"]
