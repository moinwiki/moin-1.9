# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a XMPP bot

    This is a bot for notification and simple editing
    operations. Developed as a Google Summer of Code 
    project.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import time
import Queue
from threading import Thread

from pyxmpp.client import Client
from pyxmpp.jid import JID
from pyxmpp.streamtls import TLSSettings
from pyxmpp.message import Message
from pyxmpp.presence import Presence

from xmlrpcbot import NotificationCommand

class XMPPBot(Client, Thread):
    """A simple XMPP bot"""
    
    def __init__(self, config, from_commands, to_commands):
        """A constructor.
        
        @param from_commands: a Queue object used to send commands to other (xmlrpc) threads
        @param to_commands: a Queue object used to receive commands from other threads
        """
        
        Thread.__init__(self)
        
        self.from_commands = from_commands
        self.to_commands = to_commands   
        jid = "%s@%s/%s" % (config.xmpp_node, config.xmpp_server, config.xmpp_resource)
        
        self.config = config
        self.jid = JID(node_or_jid = jid, domain = config.xmpp_server, resource = config.xmpp_resource)
        self.tlsconfig = TLSSettings(require = True, verify_peer = False)
        Client.__init__(self, self.jid, self.config.xmpp_password, self.config.xmpp_server, tls_settings = self.tlsconfig)
            
    def run(self):
        """Start the bot - enter the event loop"""
        
        if self.config:
            self.log("Starting the jabber bot.")
            
        self.connect()
        self.loop()
        
    def loop(self, timeout=1):
        """Main event loop - stream and command handling"""
        
        while 1:
            stream=self.get_stream()
            if not stream:
                break
            act=stream.loop_iter(timeout)
            if not act:
                self.poll_commands()
                self.idle()
        
    def poll_commands(self):
        """Checks for new commands in the input queue and executes them"""
        
        try:
            command = self.to_commands.get_nowait()
            self.handle_command(command)
        except Queue.Empty:
            pass
        
    def handle_command(self, command):
        """Excecutes commands from other components"""
        
        if isinstance(command, NotificationCommand):
            jid = JID(node_or_jid=command.jid)
            text = command.text
            self.send_message(jid, text)
        
    def send_message(self, to, text, type=u"chat"):
        message = Message(to_jid = to, body = text, stanza_type=type)
        self.get_stream().send(message)
    
    def handle_message(self, message):
        """Handles incoming messages"""
        
        if self.config:
            self.log( "Received a message from %s." % (message.get_from_jid().as_utf8(),) )
            
        text = message.get_body()
        sender = message.get_from_jid()
        command = text.split()
        
        # Ignore empty commands
        if len(command) == 0:
            return
        
        response = self.reply_help()
        
        if not response == u"":
            self.send_message(sender, response)
        
    def handle_presence(self):
        pass
        
    def reply_help(self):
        """Constructs a generic help message
        
        It's sent in response to an uknown message or the "help" command."""
        
        return u"""Hello there! I'm a MoinMoin Notification Bot. Too bad I can't say anything more (yet!)."""
    
    def check_availability(self, jid, type):
        """Checks if a given contacts has its availability set to "type".
        
        Possible values of the "type" argument are: away, chat, dnd, xa"""
        
        if self.roster is None or jid not in self.roster:
            return False
        
        # XXX: finish this!    
    
    def log(self, message):
        """Logs a message and its timestamp"""
        
        t = time.localtime( time.time() )
        print time.strftime("%H:%M:%S", t), message
    
    def authenticated(self):
        """Called when authentication succeedes"""
        
        if self.config:
            self.log("Authenticated.")
            
    def authorized(self):
        """Called when authorization succeedes"""
        
        if self.config:
            self.log("Authorized.")
        
        stream = self.get_stream()
        stream.set_message_handler("normal", self.handle_message)
        stream.set_presence_handler(None, self.handle_presence, "jabber:client", 0)
        
        self.request_session()
  #      self.request_roster()
        
        # Make the bot oficially available
  #      p = Presence(from_jid = stream.me, stanza_type=u"available", show=u"chat", status=self.config.status)
  #      stream.send(p)
            
    def connected(self):
        """Called when connections has been established"""
        
        if self.config:
            self.log("Connected.")
            
    def disconnected(self):
        """Called when disconnection occurs"""
        
        if self.config:
            self.log("Disconnected.")
            
    def roster_updated(self, item = None):
        """Called when roster gets updated"""
        
        if self.config:
            self.log("Updating roster.")
            
 #   def session_started(self):
 #       """Called when session has been successfully started"""
 #       
 #       if self.config.verbose:
 #           self.log("Session started.")
            
    def stream_closed(self, stream):
        """Called when stream closes"""
        
        if self.config.verbose:
            self.log("Stream closed.")
            
    def stream_created(self, stream):
        """Called when stream gets created"""
        
        if self.config.verbose:
            self.log("Stream created.")
            
    def stream_error(self, error):
        """Called when stream error gets received"""
        
        if self.config.verbose:
            self.log("Received a stream error.")
