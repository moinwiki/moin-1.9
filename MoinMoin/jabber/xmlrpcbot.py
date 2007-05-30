# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a xmlrpc server and client for the notification bot

    This is a bot for notification and simple editing
    operations. Developed as a Google Summer of Code 
    project.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from threading import Thread

class Notification:
    """Class representing a notification request"""
    
    def __init__(self, jid, text):
        self.jid = jid
        self.text = text

class XMLRPCClient(Thread):
    """XMLRPC Client
    
    It's responsible for performing XMLRPC operations on
    a wiki, as inctructed by command objects received from
    the XMPP component"""
    
    def __init__(self, commands):
        Thread.__init__(self)
        self.commands = commands

class XMLRPCServer(Thread):
    """XMLRPC Server
    
    It waits for notifications requests coming from wiki,
    creates command objects and puts them on a queue for
    later processing by the XMPP component"""
    
    def __init__(self, commands):
        Thread.__init__(self)
        self.commands = commands