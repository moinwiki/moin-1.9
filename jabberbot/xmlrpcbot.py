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

from jabberbot.commands import NotificationCommand, AddJIDToRosterCommand
from jabberbot.commands import RemoveJIDFromRosterCommand


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
        
        # Register methods having an "export" attribute as XML RPC functions and 
        # decorate them with a check for a shared (wiki-bot) secret.
        items = self.__class__.__dict__.items()
        methods = [(name, func) for (name, func) in items if callable(func) 
                   and "export" in func.__dict__]

        for name, func in methods:
            self.server.register_function(self.secret_check(func), name)
        
        self.server.serve_forever()
        
    def log(self, message):
        """Logs a message and its timestamp"""
        
        t = time.localtime( time.time() )
        print time.strftime("%H:%M:%S", t), message

    def secret_check(self, function):
        """Adds a check for a secret to a given function
        
        Using this one does not have to worry about checking for the secret
        in every XML RPC function.
        """
        def protected_func(secret, *args):
            if secret != self.secret:
                raise xmlrpclib.Fault(1, "You are not allowed to use this bot!")
            else:
                return function(self, *args)
            
        return protected_func
    
    
    def send_notification(self, jid, text):
        """Instructs the XMPP component to send a notification"""           
        c = NotificationCommand(jid, text)
        self.commands.put_nowait(c)
        return True
    send_notification.export = True
    
    def addJIDToRoster(self, jid):
        """Instructs the XMPP component to add a new JID to its roster"""  
        c = AddJIDToRosterCommand(jid)
        self.commands.put_nowait(c)
        return True
    addJIDToRoster.export = True
    
    def removeJIDFromRoster(self, jid):
        """Instructs the XMPP component to remove a JID from its roster"""      
        c = RemoveJIDFromRosterCommand(jid)
        self.commands.put_nowait(c)
        return True
    removeJIDFromRoster.export = True
