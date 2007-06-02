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

from xmlrpcbot import NotificationCommand

class Contact:
    """Abstraction of a roster item / contact
 
    This class handles some logic related to keeping track of
    contact availability, status, etc."""
    
    def __init__(self, jid, resource, priority, show):
        self.jid = jid
        self.resources = [{'resource': resource, 'show': show, 'priority': priority}]

        # Queued messages, waiting for contact to change its "show"
        # status to something different than "dnd". The messages should
        # also be sent when contact becomes "unavailable" directly from
        # "dnd", as we can't guarantee, that the bot will be up and running
        # the next time she becomes "available".
        self.messages = []
        
    def add_resource(self, resource, show, priority):
        """Adds information about a connected resource"""
        res = {'resource': resource, 'show': show, 'priority': priority}
        self.resources.append(res)
    
    def remove_resource(self, resource):
        """Removes information about a connected resource"""
        for i in xrange(len(self.resources)):
            if self.resources[i]['resource'] == resource:
                del self.resources[i]
                return
        else:
            raise ValueError("No such resource!")
        
    def is_dnd(self):
        """Checks if contact is DoNotDisturb
        
        The contact is DND if its resource with the highest priority is DND
        """
        
        max_prio = self.resources[0]['priority']
        max_prio_show = self.resources[0]['show']
        
        for res in self.resources:
            # TODO: check RFC for behaviour of 2 resources with the same priority
            if res['priority'] > max_prio:
                max_prio = res['priority']
                max_prio_show = res['show']
                
        if max_prio_show == u'dnd':
            return True
        else:
            return False
        
    def set_show(self, resource, show):
        """Sets show property for a given resource
        
        @param resource: resource to alter
        @param show: new value of the show property
        @raise ValueError: no resource with given name has been found
        """
        for res in self.resources:
            if res['resource'] == resource:
                res['show'] = show
        else:
            raise ValueError("There's no such resource")
    
    def uses_resource(self, resource):
        """Checks if contact uses a given resource"""
    
        for res in self.resources:
            if res['resource'] == resource: 
                return True
        else:
            return False        
        
    def __str__(self):
        retval = "%s (%s) has %d queued messages"
        resources = ", ".join([r['resource'] + " is " + r['show'] for r in self.resources])
        return retval % (self.jid.as_utf8(), resources, len(self.messages))


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
        jid = u"%s@%s/%s" % (config.xmpp_node, config.xmpp_server, config.xmpp_resource)
        
        self.config = config
        self.jid = JID(node_or_jid=jid, domain=config.xmpp_server, resource=config.xmpp_resource)
        self.tlsconfig = TLSSettings(require = True, verify_peer = False)
        
        # A dictionary of contact objects, ordered by bare JID
        self.contacts = { }
        
        Client.__init__(self, self.jid, config.xmpp_password, config.xmpp_server, tls_settings = self.tlsconfig)
            
    def run(self):
        """Start the bot - enter the event loop"""
        
        if self.config.verbose:
            self.log("Starting the jabber bot.")
            
        self.connect()
        self.loop()
        
    def loop(self, timeout=1):
        """Main event loop - stream and command handling"""
        
        while 1:
            stream = self.get_stream()
            if not stream:
                break
            
            act = stream.loop_iter(timeout)
            if not act:
                # Process all available commands
                while self.poll_commands(): pass
                self.idle()
        
    def poll_commands(self):
        """Checks for new commands in the input queue and executes them
        
        @return: True if any command has been executed, False otherwise."""
        
        try:
            command = self.to_commands.get_nowait()
            self.handle_command(command)
            return True
        except Queue.Empty:
            return False
        
    def handle_command(self, command, ignore_dnd = False):
        """Excecutes commands from other components"""
        
        if isinstance(command, NotificationCommand):
            jid = JID(node_or_jid=command.jid)
            jid_text = jid.bare().as_utf8()
            text = command.text
            
            # Check if contact is DoNotDisturb. 
            # If so, queue the message for delayed delivery.
            try:
                contact = self.contacts[jid_text]
                if contact.is_dnd() and not ignore_dnd:
                    contact.messages.append(command)
                    return
            except KeyError:
                pass
            
            self.send_message(jid, text)
        
    def send_message(self, jid, text, msg_type=u"chat"):
        """Sends a message
        
        @param jid: JID to send the message to
        @param text: message's body
        @param type: message type, as defined in RFC"""
        
        message = Message(to_jid = jid, body = text, stanza_type=msg_type)
        self.get_stream().send(message)
    
    def handle_message(self, message):
        """Handles incoming messages"""
        
        if self.config.verbose:
            msg = "Message from %s." % (message.get_from_jid().as_utf8(),)
            self.log(msg)
            
        text = message.get_body()
        sender = message.get_from_jid()
        command = text.split()
        
        # Ignore empty commands
        if len(command) == 0:
            return
        
        response = self.reply_help()
        
        if not response == u"":
            self.send_message(sender, response)
        
    def handle_unavailable_presence(self, stanza):
        """Handles unavailable presence stanzas"""
        
        if self.config.verbose:
            self.log("Handling unavailable presence.")
        
        jid = stanza.get_from_jid()
        bare_jid = jid.bare().as_utf8()
        
        # If we get presence, this contact should already be known
        if bare_jid in self.contacts:    
            contact = self.contacts[bare_jid]
            
            if self.config.verbose:
                self.log(str(contact) + ", going OFFLINE.")
            
            try:
                # Send queued messages now, as we can't guarantee to be 
                # alive the next time this contact becomes available.
                if len(contact.resources) == 1:    
                    self.send_queued_messages(contact, ignore_dnd=True)
                    del self.contacts[bare_jid]
                else:
                    contact.remove_resource(jid.resource)
                    
                    # The highest-priority resource, which used to be DnD might
                    # have gone offline. If so, try to deliver messages now.
                    if not contact.is_dnd():
                        self.send_queued_messages(contact)
                    
            except ValueError:
                self.log("Unknown contact (resource) going offline...")
            
        else:
            self.log("Unavailable presence from unknown contact.")
                
        # Confirm that we've handled this stanza
        return True
    
    def handle_available_presence(self, presence):
        """Handles available presence stanzas"""
        if self.config.verbose:
            self.log("Handling available presence.")
        
        show = presence.get_show()
        priority = presence.get_priority()
        jid = presence.get_from_jid()
        bare_jid = jid.bare().as_utf8()
               
        if bare_jid in self.contacts:    
            contact = self.contacts[bare_jid]
            
            if self.config.verbose:
                self.log(contact)                
                
            # The resource is already known, so update it
            if contact.uses_resource(bare_jid):
                contact.set_show(bare_jid, show)
            
            # Unknown resource, add it to the list
            else:
                contact.add_resource(jid.resource, show, priority)

            # Either way check, if we can deliver queued messages now
            if not contact.is_dnd():
                self.send_queued_messages(contact)
                
        else:
            self.contacts[bare_jid] = Contact(jid, jid.resource, priority, show)
            
            if self.config.verbose:
                self.log(self.contacts[bare_jid])
        
        # Confirm that we've handled this stanza
        return True
    
    def send_queued_messages(self, contact, ignore_dnd = False):
        """Sends messages queued for the contact"""
        for command in contact.messages:
            self.handle_command(command, ignore_dnd)
                    
    def reply_help(self):
        """Constructs a generic help message
        
        It's sent in response to an uknown message or the "help" command."""
        
        return u"""Hello there! I'm a MoinMoin Notification Bot. Too bad I can't say anything more (yet!)."""
    
    def log(self, message):
        """Logs a message and its timestamp"""
        
        t = time.localtime( time.time() )
        print time.strftime("%H:%M:%S", t), message
    
    def authenticated(self):
        """Called when authentication succeedes"""
        
        if self.config.verbose:
            self.log("Authenticated.")
            
    def authorized(self):
        """Called when authorization succeedes"""
        
        if self.config.verbose:
            self.log("Authorized.")
        
        stream = self.get_stream()
        stream.set_message_handler("normal", self.handle_message)
        stream.set_presence_handler("available", self.handle_available_presence)
        stream.set_presence_handler("unavailable", self.handle_unavailable_presence)
        
        self.request_session()
            
    def connected(self):
        """Called when connections has been established"""
        
        if self.config.verbose:
            self.log("Connected.")
            
    def disconnected(self):
        """Called when disconnection occurs"""
        
        if self.config.verbose:
            self.log("Disconnected.")
            
    def roster_updated(self, item = None):
        """Called when roster gets updated"""
        
        if self.config.verbose:
            self.log("Updating roster.")
            
            contacts = [ str(c) for c in self.roster.get_items() ]
            print "Groups:", self.roster.get_groups()
            print "Contacts:", " ".join(contacts)
            
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
