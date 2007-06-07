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
