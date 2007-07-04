# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import logging, time, Queue
from threading import Thread

from pyxmpp.client import Client
from pyxmpp.jid import JID
from pyxmpp.streamtls import TLSSettings
from pyxmpp.message import Message
from pyxmpp.presence import Presence

import jabberbot.commands as cmd

class Contact:
    """Abstraction of a roster item / contact

    This class handles some logic related to keeping track of
    contact availability, status, etc."""

    def __init__(self, jid, resource, priority, show):
        self.jid = jid
        self.resources = {resource: {'show': show, 'priority': priority}}

        # Queued messages, waiting for contact to change its "show"
        # status to something different than "dnd". The messages should
        # also be sent when contact becomes "unavailable" directly from
        # "dnd", as we can't guarantee, that the bot will be up and running
        # the next time she becomes "available".
        self.messages = []

    def add_resource(self, resource, show, priority):
        """Adds information about a connected resource

        @param resource: resource name
        @param show: a show presence property, as defined in XMPP
        @param priority: priority of the given resource

        """
        self.resources[resource] = {'show': show, 'priority': priority}
    
    def remove_resource(self, resource):
        """Removes information about a connected resource
        
        @param resource: resource name
        
        """
        if self.resources.has_key(resource):
            del self.resources[resource]
        else:
            raise ValueError("No such resource!")
        
    def is_dnd(self):
        """Checks if contact is DoNotDisturb
        
        The contact is DND if its resource with the highest priority is DND
        
        """      
        # Priority can't be lower than -128
        max_prio = -129
        max_prio_show = u"dnd"
        
        for resource in self.resources.itervalues():
            # TODO: check RFC for behaviour of 2 resources with the same priority
            if resource['priority'] > max_prio:
                max_prio = resource['priority']
                max_prio_show = resource['show']
                
        return max_prio_show == u'dnd'
        
    def set_show(self, resource, show):
        """Sets show property for a given resource
        
        @param resource: resource to alter
        @param show: new value of the show property
        @raise ValueError: no resource with given name has been found
        
        """
        if self.resources.has_key(resource):
            self.resources[resource]['show'] = show
        else:
            raise ValueError("There's no such resource")
    
    def uses_resource(self, resource):
        """Checks if contact uses a given resource"""
        return self.resources.has_key(resource)
        
    def __str__(self):
        retval = "%s (%s) has %d queued messages"
        res = ", ".join([name + " is " + res['show'] for name, res in self.resources.items()])
        return retval % (self.jid.as_utf8(), res, len(self.messages))


class XMPPBot(Client, Thread):
    """A simple XMPP bot"""
       
    def __init__(self, config, from_commands, to_commands):
        """A constructor
        
        @param from_commands: a Queue object used to send commands to other (xmlrpc) threads
        @param to_commands: a Queue object used to receive commands from other threads
        
        """
        Thread.__init__(self)
        
        self.from_commands = from_commands
        self.to_commands = to_commands   
        jid = u"%s@%s/%s" % (config.xmpp_node, config.xmpp_server, config.xmpp_resource)
        
        self.config = config
        self.log = logging.getLogger("log")
        self.jid = JID(node_or_jid=jid, domain=config.xmpp_server, resource=config.xmpp_resource)
        self.tlsconfig = TLSSettings(require = True, verify_peer=False)
        
        # A dictionary of contact objects, ordered by bare JID
        self.contacts = {}

        self.known_xmlrpc_cmds = [cmd.GetPage, cmd.GetPageHTML, cmd.GetPageList, cmd.GetPageInfo] 
        self.internal_commands = ["ping", "help"]
        
        self.xmlrpc_commands = {}
        for command, name in [(command, command.__name__) for command in self.known_xmlrpc_cmds]:
            self.xmlrpc_commands[name] = command
        
        Client.__init__(self, self.jid, config.xmpp_password, config.xmpp_server, tls_settings=self.tlsconfig)   
    
    def run(self):
        """Start the bot - enter the event loop"""
        
        self.log.info("Starting the jabber bot.")    
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
        
        @return: True if any command has been executed, False otherwise.
        
        """
        try:
            command = self.to_commands.get_nowait()
            self.handle_command(command)
            return True
        except Queue.Empty:
            return False
        
    def handle_command(self, command, ignore_dnd=False):
        """Excecutes commands from other components
        
        @param command: a command to execute
        @type command: any class defined in commands.py (FIXME?)
        @param ignore_dnd: if command results in user interaction, should DnD be ignored?
        
        """
        # Handle normal notifications
        if isinstance(command, cmd.NotificationCommand):
            for recipient in command.jids:
                jid = JID(recipient)
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
            
        # Handle subscribtion management commands
        if isinstance(command, cmd.AddJIDToRosterCommand):
            jid = JID(node_or_jid=command.jid)
            self.ask_for_subscription(jid)
            
        elif isinstance(command, cmd.RemoveJIDFromRosterCommand):
            jid = JID(node_or_jid=command.jid)
            self.remove_subscription(jid)
            
        elif isinstance(command, cmd.GetPage) or isinstance(command, cmd.GetPageHTML):
            msg = u"""Here's the page "%s" that you've requested:\n\n%s"""
            self.send_message(command.jid, msg % (command.pagename, command.data))
        
        elif isinstance(command, cmd.GetPageList):
            msg = u"""That's the list of pages accesible to you:\n\n%s"""
            pagelist = "\n".join(command.data)
            self.send_message(command.jid, msg % (pagelist, ))
            
        elif isinstance(command, cmd.GetPageInfo):
            msg = u"""Following detailed information on page "%s" is available::\n\n%s"""
            self.send_message(command.jid, msg % (command.pagename, command.data))
            
    def ask_for_subscription(self, jid):
        """Sends a <presence/> stanza with type="subscribe"
        
        Bot tries to subscribe to every contact's presence, so that
        it can honor special cases, like DoNotDisturb setting.
        
        @param jid: Jabber ID of entity we're subscribing to
        @type jid: pyxmpp.jid.JID
        
        """
        stanza = Presence(to_jid=jid, stanza_type="subscribe")
        self.get_stream().send(stanza)
        
    def remove_subscription(self, jid):
        """Sends a <presence/> stanza with type="unsubscribed
        
        @param jid: Jabber ID of entity whose subscription we cancel
        @type jid: JID
        
        """
        stanza = Presence(to_jid=jid, stanza_type="unsubscribed")
        self.get_stream().send(stanza)
        
    def send_message(self, jid, text, msg_type=u"chat"):
        """Sends a message
        
        @param jid: JID to send the message to
        @param text: message's body: 
        @param type: message type, as defined in RFC
        @type jid: pyxmpp.jid.JID
        
        """
        message = Message(to_jid=jid, body=text, stanza_type=msg_type)
        self.get_stream().send(message)
    
    def handle_message(self, message):
        """Handles incoming messages
        
        @param message: a message stanza to parse
        @type message: pyxmpp.message.Message
        
        """    
        if self.config.verbose:
            msg = "Message from %s." % (message.get_from_jid().as_utf8(), )
            self.log.debug(msg)
            
        text = message.get_body()
        sender = message.get_from_jid()
        command = text.split()
        
        # Ignore empty commands
        if not command:
            return
        
        if command[0] in self.internal_commands:
            response = self.handle_internal_command(command)
        elif command[0] in self.xmlrpc_commands.keys():
            response = self.handle_xmlrpc_command(sender, command)
        else:
            response = self.reply_help()
        
        if not response == u"":
            self.send_message(sender, response)
            
    def handle_internal_command(self, command):
        """Handles internal commands, that can be completed by the XMPP bot itself
        
        @param command: list representing a command
        
        """
        if command[0] == "ping":
            return "pong"
        elif command[0] == "help":
            if len(command) == 1:
                return self.reply_help()
            else:
                return self.help_on(command[1])
        else:
            # For unknown command return a generic help message
            return self.reply_help()
        
    def help_on(self, command):
        """Returns a help message on a given topic
        
        @param command: a command to describe in a help message
        @type command: str or unicode
        @return: a help message
        
        """
        if command == "help":
            return u"""The "help" command prints a short, helpful message about a given topic or function.\n\nUsage: help [topic_or_function]"""
        
        elif command == "ping":
            return u"""The "ping" command returns a "pong" message as soon as it's received."""
        
        # Here we have to deal with help messages of external (xmlrpc) commands
        else:
            classobj = self.xmlrpc_commands[command]
            help_str = u"%s - %s\n\nUsage: %s %s"
            return help_str % (command, classobj.description, command, classobj.parameter_list)
        
        
    def handle_xmlrpc_command(self, sender, command):
        """Creates a command object, and puts it the command queue
        
        @param command: a valid name of available xmlrpc command
        @type command: list representing a command, name and parameters
        
        """
        command_class = self.xmlrpc_commands[command[0]]
        
        # Add sender's JID to the argument list
        command.insert(1, sender.as_utf8())
        
        try:
            instance = command_class.__new__(command_class)
            instance.__init__(*command[1:])
            self.from_commands.put_nowait(instance)
            
        # This happens when user specifies wrong parameters
        except TypeError:
            msg = u"You've specified a wrong parameter list. The call should look like:\n\n%s %s"
            return msg % (command[0], command_class.parameter_list)
            
    def handle_unsubscribed_presence(self, stanza):
        """Handles unsubscribed presence stanzas"""
        
        # FiXME: what policy should we adopt in this case?
        pass
    
    def handle_subscribe_presence(self, stanza):
        """Handles subscribe presence stanzas (requests)"""
        
        # FIXME: Let's just accept all subscribtion requests for now
        response = stanza.make_accept_response()
        self.get_stream().send(response)
        
    def handle_unavailable_presence(self, stanza):
        """Handles unavailable presence stanzas
        
        @type stanza: pyxmpp.presence.Presence
        
        """
        self.log.debug("Handling unavailable presence.")
        
        jid = stanza.get_from_jid()
        bare_jid = jid.bare().as_utf8()
        
        # If we get presence, this contact should already be known
        if bare_jid in self.contacts:    
            contact = self.contacts[bare_jid]
            
            if self.config.verbose:
                self.log.debug("%s, going OFFLINE." % contact)
            
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
                self.log.error("Unknown contact (resource) going offline...")
            
        else:
            self.log.error("Unavailable presence from unknown contact.")
                
        # Confirm that we've handled this stanza
        return True
    
    def handle_available_presence(self, presence):
        """Handles available presence stanzas
        
        @type presence: pyxmpp.presence.Presence
        
        """
        self.log.debug("Handling available presence.")
        
        show = presence.get_show()
        if show is None:
            show = u'available'
            
        priority = presence.get_priority()
        jid = presence.get_from_jid()
        bare_jid = jid.bare().as_utf8()
               
        if bare_jid in self.contacts:    
            contact = self.contacts[bare_jid]              
                
            # The resource is already known, so update it
            if contact.uses_resource(jid.resource):
                contact.set_show(jid.resource, show)
            
            # Unknown resource, add it to the list
            else:
                contact.add_resource(jid.resource, show, priority)

            if self.config.verbose:
                self.log.debug(contact)

            # Either way check, if we can deliver queued messages now
            if not contact.is_dnd():
                self.send_queued_messages(contact)
                
        else:
            self.contacts[bare_jid] = Contact(jid, jid.resource, priority, show)
            self.log.debug(self.contacts[bare_jid])
        
        # Confirm that we've handled this stanza
        return True
    
    def send_queued_messages(self, contact, ignore_dnd=False):
        """Sends messages queued for the contact
        
        @param contact: a contact whose queued messages are to be sent
        @type contact: jabberbot.xmppbot.Contact
        @param ignore_dnd: should contact's DnD status be ignored?
        
        """
        for command in contact.messages:
            self.handle_command(command, ignore_dnd)
                    
    def reply_help(self):
        """Constructs a generic help message
        
        It's sent in response to an uknown message or the "help" command.
        
        """
        msg = u"""Hello there! I'm a MoinMoin Notification Bot. Available commands:\n\n%s\n%s"""
        internal = ", ".join(self.internal_commands)
        xmlrpc = ", ".join(self.xmlrpc_commands.keys())
        
        return msg % (internal, xmlrpc)
    
    def authenticated(self):
        """Called when authentication succeedes"""
        self.log.info("Authenticated.")
            
    def authorized(self):
        """Called when authorization succeedes"""
        
        self.log.info("Authorized.")
        
        stream = self.get_stream()
        stream.set_message_handler("normal", self.handle_message)
        stream.set_presence_handler("available", self.handle_available_presence)
        stream.set_presence_handler("unavailable", self.handle_unavailable_presence)
        stream.set_presence_handler("unsubscribed", self.handle_unsubscribed_presence)
        stream.set_presence_handler("subscribe", self.handle_subscribe_presence)
        
        self.request_session()
            
    def connected(self):
        """Called when connections has been established"""
        self.log.info("Connected.")
            
    def disconnected(self):
        """Called when disconnection occurs"""
        self.log.info("Disconnected.")
            
    def roster_updated(self, item=None):
        """Called when roster gets updated"""
        self.log.debug("Updating roster.")
            
    def stream_closed(self, stream):
        """Called when stream closes"""
        self.log.debug("Stream closed.")
            
    def stream_created(self, stream):
        """Called when stream gets created"""
        self.log.debug("Stream created.")
            
    def stream_error(self, error):
        """Called when stream error gets received"""
        self.log.error("Received a stream error.")
