# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - event (notification) framework

    This code abstracts event handling in MoinMoin,
    currently for notifications. It implements the observer pattern.

@copyright: 2007 by Karol Nowak <grywacz@gmail.com>
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.util import pysupport

# A list of available event handlers
event_handlers = None

# Create a list of extension actions from the package directory
modules = pysupport.getPackageModules(__file__)

class Event:
    """A class handling information common to all events."""
    
    def __init__(self, request, page):
        self.request = request
        self.page = page
        
class PageChangedEvent(Event):
    pass

class PageRenamedEvent(Event):
    pass

class PageDeletedEvent(Event):
    pass
        
def register_handlers(cfg):
    """Create a list of available event handlers.
    
    Each handler is a handle() function defined in an plugin,
    pretty much like in case of actions.
    
    TODO: maybe make it less dumb? ;-)"""
    
    global event_handlers

    event_handlers = []
    names = wikiutil.getPlugins("events", cfg)

    for name in names:
        handler = wikiutil.importPlugin(cfg, "events", name, "handle")
        
        if handler is not None:
            event_handlers.append(handler)

def send_event(event):
    """Function called from outside to process an event"""
    
    # Find all available event handlers
    if event_handlers is None:
        register_handlers(event.request.cfg)
    
    # Try to handle the event with each available handler (for now)
    for handle in event_handlers:
        handle(event)