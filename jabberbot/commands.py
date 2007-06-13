# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - inter-thread communication commands

    This file defines command objects used by notification
    bot's threads to communicate among each other.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

# First, XML RPC -> XMPP commands
class NotificationCommand:
    """Class representing a notification request"""
    def __init__(self, jid, text):
        self.jid = jid
        self.text = text
        
class AddJIDToRosterCommand:
    """Class representing a request to add a new jid to roster"""
    def __init__(self, jid):
        self.jid = jid
        
class RemoveJIDFromRosterCommand:
    """Class representing a request to remove a jid from roster"""
    def __init__(self, jid):
        self.jid = jid

# XMPP <-> XML RPC commands
# These commands are passed in both directions, with added data
# payload when they return to the XMPP code. Naming convention
# follows method names defined by the Wiki RPC Interface v2.

class BaseDataCommand(object):
    """Base class for all commands used by the XMPP component.
    
    It has to support an optional data payload and store JID the
    request has come from and provide a help string for its parameters.
    """
    
    # Description of what the command does
    description = u""
    
    # Parameter list in a human-readable format
    parameter_list = u""
    
    def __init__(self, jid):
        self.jid = jid
        self.data = None
        
class GetPage(BaseDataCommand):
    
    description = u"retrieve raw content of a named page"
    parameter_list = u"pagename"
    
    def __init__(self, jid, pagename):
        BaseDataCommand.__init__(self, jid)
        self.pagename = pagename
        
class GetPageHTML(BaseDataCommand):
    
    description = u"retrieve HTML-formatted content of a named page"
    parameter_list = u"pagename"
    
    def __init__(self, jid, pagename):
        BaseDataCommand.__init__(self, jid)
        self.pagename = pagename