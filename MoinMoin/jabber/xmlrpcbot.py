# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a xmlrpc server and client for the notification bot

    This is a bot for notification and simple editing
    operations. Developed as a Google Summer of Code 
    project.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import time
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
        Thread.__init__(self)
        self.commands = commands
        
    def run(self):
        pass

class XMLRPCServer(Thread, SimpleXMLRPCServer):
    """XMLRPC Server
    
    It waits for notifications requests coming from wiki,
    creates command objects and puts them on a queue for
    later processing by the XMPP component"""
    
    def __init__(self, config, commands):
        Thread.__init__(self)
        SimpleXMLRPCServer.__init__(self, (config.xmlrpc_host, config.xmlrpc_port) )
        self.commands = commands
        self.verbose = config.verbose
        
    def run(self):
        """Starts the server / thread"""
        
        self.register_function(self.send_notification)
        self.serve_forever()
        
    def log(self, message):
        """Logs a message and its timestamp"""
        
        t = time.localtime( time.time() )
        print time.strftime("%H:%M:%S", t), message

    def send_notification(self, jid, text):
        """Instructs the XMPP component to send a notification"""
        
        n = NotificationCommand(jid, text)
        self.commands.put_nowait(n)
        return True
