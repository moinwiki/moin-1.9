# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a xmlrpc server and client for the notification bot

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import Queue
import time, xmlrpclib
from threading import Thread
from SimpleXMLRPCServer import SimpleXMLRPCServer

import jabberbot.commands as cmd
from jabberbot.multicall import MultiCall


class XMLRPCClient(Thread):
    """XMLRPC Client
    
    It's responsible for performing XMLRPC operations on
    a wiki, as inctructed by command objects received from
    the XMPP component"""
    
    def __init__(self, config, commands_in, commands_out):
        """
        @param commands: an output command queue
        """
        Thread.__init__(self)
        self.commands_in = commands_in
        self.commands_out = commands_out
        self.config = config
        self.url = config.wiki_url + "?action=xmlrpc2"
        self.connection = self.create_connection()
        self.token = None
        self.multicall = None

    def run(self):
        """Starts the server / thread"""
        while True:
            try:
                command = self.commands_in.get(True, 2)
                self.execute_command(command)
            except Queue.Empty:
                pass
            
    def create_connection(self):
        return xmlrpclib.ServerProxy(self.url, allow_none=True, verbose=self.config.verbose)
                
    def execute_command(self, command):
        """Execute commands coming from the XMPP component"""
        
        # FIXME: make this kind of automatic
        if isinstance(command, cmd.GetPage):
            self.get_page(command)
        elif isinstance(command, cmd.GetPageHTML):
            self.get_page_html(command)
        elif isinstance(command, cmd.GetPageList):
            self.get_page_list(command)
    
    def get_auth_token(self, jid):
        token = self.connection.getAuthToken(jid, self.config.secret)
        if token:
            self.token = token
    
    def get_page(self, command):
        self.token = None
        self.multicall = MultiCall(self.connection)
        self.get_auth_token(command.jid)
            
        if not self.token:
            # FIXME: notify the user that he may not have full rights on the wiki
            self.multicall.getPage(command.pagename)
            getpage_result = self.multicall()
        else:
            self.multicall.applyAuthToken(self.token)
            self.multicall.getPage(command.pagename)
            token_result, getpage_result = self.multicall()

        # We get a dict only when Fault happens
        if isinstance(getpage_result[0], dict):
            error_str = u"""The page couldn't be retrieved. The reason is: "%s"."""
            command.data = error_str % getpage_result[0]["faultString"]
        else:
            command.data = getpage_result[0]
     
        self.commands_out.put_nowait(command)
        
        del self.multicall
        del self.token
        
    def get_page_html(self, command):
        self.token = None
        self.multicall = MultiCall(self.connection)
        self.get_auth_token(command.jid)
            
        if not self.token:
            # FIXME: notify the user that he may not have full rights on the wiki
            self.multicall.getPageHTML(command.pagename)
            getpage_result = self.multicall()
        else:
            self.multicall.applyAuthToken(self.token)
            self.multicall.getPageHTML(command.pagename)
            token_result, getpage_result = self.multicall()

        # We get a dict only when Fault happens
        if isinstance(getpage_result[0], dict):
            error_str = u"""The page couldn't be retrieved. The reason is: "%s"."""
            command.data = error_str % getpage_result[0]["faultString"]
        else:
            command.data = getpage_result[0]
     
        self.commands_out.put_nowait(command)
        
        del self.multicall
        del self.token
        
    def get_page_list(self, command):
        self.token = None
        self.multicall = MultiCall(self.connection)
        self.get_auth_token(command.jid)
        
        txt = u"""This command may take a while to complete, please be patient..."""
        info = cmd.NotificationCommand(command.jid, txt)
        self.commands_out.put_nowait(info)
        
        if not self.token:
            # FIXME: notify the user that he may not have full rights on the wiki
            self.multicall.getAllPages()
            getpage_result = self.multicall()
        else:
            self.multicall.applyAuthToken(self.token)
            self.multicall.getAllPages()
            token_result, getpage_result = self.multicall()

        # We get a dict only when Fault happens
        if isinstance(getpage_result[0], dict):
            error_str = u"""List couldn't be retrieved. The reason is: "%s"."""
            command.data = error_str % getpage_result[0]["faultString"]
        else:
            command.data = getpage_result[0]
     
        self.commands_out.put_nowait(command)
        
        del self.multicall
        del self.token


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
        """Instructs the XMPP component to send a notification
        
        @param jid: a jid to send a message to (bare jid)
        @type jid: str or unicode
        @param text: a message body
        @type text: unicode
        
        """
        c = cmd.NotificationCommand(jid, text)
        self.commands.put_nowait(c)
        return True
    send_notification.export = True
    
    def addJIDToRoster(self, jid):
        """Instructs the XMPP component to add a new JID to its roster
        
        @param jid: a jid to add, this must be a bare jid
        @type jid: str or unicode, 
        
        """  
        c = cmd.AddJIDToRosterCommand(jid)
        self.commands.put_nowait(c)
        return True
    addJIDToRoster.export = True
    
    def removeJIDFromRoster(self, jid):
        """Instructs the XMPP component to remove a JID from its roster
        
        @param jid: a jid to remove, this must be a bare jid
        @type jid: str or unicode
        
        """
        c = cmd.RemoveJIDFromRosterCommand(jid)
        self.commands.put_nowait(c)
        return True
    removeJIDFromRoster.export = True
