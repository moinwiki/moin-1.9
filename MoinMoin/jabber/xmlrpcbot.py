# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a xmlrpc server and client for the notification bot

    This is a bot for notification and simple editing
    operations. Developed as a Google Summer of Code 
    project.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import time, xmlrpclib
from threading import Thread
from SimpleXMLRPCServer import SimpleXMLRPCServer


class NotificationCommand:
    """Class representing a notification request"""
    
    def __init__(self, jid, text):
        self.jid = jid
        self.text = text


class XMLRPCClient(Thread):
    """XMLRPC Client
    
    It's responsible for performing XMLRPC operations on
    a wiki, as inctructed by command objects received from
    the XMPP component"""
    
    def __init__(self, config, commands):
        """
        @param commands: an output command queue
        """
        Thread.__init__(self)
        self.commands = commands
        self.config = config
        
    def run(self):
        """Starts the server / thread"""
        pass


class XMLRPCServer(Thread):
    """XMLRPC Server
    
    It waits for notifications requests coming from wiki,
    creates command objects and puts them on a queue for
    later processing by the XMPP component
    
    @param commands: an input command queue
    """
    
    def __init__(self, config, commands):
        Thread.__init__(self)
        self.commands = commands
        self.verbose = config.verbose
        self.secret = config.secret
        self.server = SimpleXMLRPCServer((config.xmlrpc_host, config.xmlrpc_port))
        
    def run(self):
        """Starts the server / thread"""
        
        self.server.register_function(self.send_notification)
        self.server.serve_forever()
        
    def log(self, message):
        """Logs a message and its timestamp"""
        
        t = time.localtime( time.time() )
        print time.strftime("%H:%M:%S", t), message

    def send_notification(self, secret, jid, text):
        """Instructs the XMPP component to send a notification"""
        
        if secret != self.secret:
            raise xmlrpclib.Fault(1, "You are not allowed to use this bot!")
            
        n = NotificationCommand(jid, text)
        self.commands.put_nowait(n)
        return True
