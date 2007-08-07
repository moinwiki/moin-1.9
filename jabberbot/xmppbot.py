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
from pyxmpp.iq import Iq
import pyxmpp.jabber.dataforms as forms

import jabberbot.commands as cmd
import jabberbot.i18n as i18n
import jabberbot.oob as oob


class Contact:
    """Abstraction of a roster item / contact

    This class handles some logic related to keeping track of
    contact availability, status, etc."""

    # Default Time To Live of a contact. If there are no registered
    # resources for that period of time, the contact should be removed
    default_ttl = 3600 * 24 # default of one day

    def __init__(self, jid, resource, priority, show, language=None):
        self.jid = jid
        self.resources = {resource: {'show': show, 'priority': priority}}
        self.language = language

        # The last time when this contact was seen online.
        # This value has meaning for offline contacts only.
        self.last_online = None

        # Queued messages, waiting for contact to change its "show"
        # status to something different than "dnd". The messages should
        # also be sent when contact becomes "unavailable" directly from
        # "dnd", as we can't guarantee, that the bot will be up and running
        # the next time she becomes "available".
        self.messages = []

    def is_valid(self, current_time):
        """Check if this contact entry is still valid and should be kept

        @param time: current time in seconds

        """
        # No resources == offline
        return self.resources or current_time < self.last_online + self.default_ttl

    def add_resource(self, resource, show, priority):
        """Adds information about a connected resource

        @param resource: resource name
        @param show: a show presence property, as defined in XMPP
        @param priority: priority of the given resource

        """
        self.resources[resource] = {'show': show, 'priority': priority, 'forms': False}
        self.last_online = None

    def set_supports(self, resource, extension):
        """Flag a given resource as supporting a particular extension"""
        if resource in self.resources:
            self.resources[resource][extension] = True

    def supports(self, resource, extension):
        """Check if a given resource supports a particular extension"""
        if resource in self.resources:
            return extension in self.resources[resource]

    def remove_resource(self, resource):
        """Removes information about a connected resource

        @param resource: resource name

        """
        if self.resources.has_key(resource):
            del self.resources[resource]
        else:
            raise ValueError("No such resource!")

        if not self.resources:
            self.last_online = time.time()

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

        # If there are no resources the contact is offline, not dnd
        return self.resources and max_prio_show == u'dnd'

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

        # The last time when contacts were checked for expiration, in seconds
        self.last_expiration = time.time()

        # How often should the contacts be checked for expiration, in seconds
        self.contact_check = 600

        self.known_xmlrpc_cmds = [cmd.GetPage, cmd.GetPageHTML, cmd.GetPageList, cmd.GetPageInfo, cmd.Search]
        self.internal_commands = ["ping", "help", "searchform"]

        self.xmlrpc_commands = {}
        for command, name in [(command, command.__name__) for command in self.known_xmlrpc_cmds]:
            self.xmlrpc_commands[name.lower()] = command

        Client.__init__(self, self.jid, config.xmpp_password, config.xmpp_server, tls_settings=self.tlsconfig)

    def run(self):
        """Start the bot - enter the event loop"""

        self.log.info("Starting the jabber bot.")
        self.connect()
        self.loop()

    def loop(self, timeout=1):
        """Main event loop - stream and command handling"""

        while True:
            stream = self.get_stream()
            if not stream:
                break

            act = stream.loop_iter(timeout)
            if not act:
                # Process all available commands
                while self.poll_commands(): pass
                self.idle()

    def idle(self):
        """Do some maintenance"""

        Client.idle(self)

        current_time = time.time()
        if self.last_expiration + self.contact_check < current_time:
            self.expire_contacts(current_time)
            self.last_expiration = current_time

    def expire_contacts(self, current_time):
        """Check which contats have been offline for too long and should be removed

        @param current_time: current time in seconds

        """
        for jid, contact in self.contacts.items():
            if not contact.is_valid(current_time):
                del self.contacts[jid]

    def get_text(self, jid):
        """Returns a gettext function (_) for the given JID

        @param jid: bare Jabber ID of the user we're going to communicate with
        @type jid: str or pyxmpp.jid.JID

        """
        language = "en"
        if isinstance(jid, str) or isinstance(jid, unicode):
            jid = JID(jid).bare().as_utf8()
        else:
            jid = jid.bare().as_utf8()

        if jid in self.contacts:
            language = self.contacts[jid].language

        return lambda text: i18n.get_text(text, lang=language)

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

    # XXX: refactor this, if-elif sequence is already too long
    def handle_command(self, command, ignore_dnd=False):
        """Excecutes commands from other components

        @param command: a command to execute
        @type command: any class defined in commands.py (FIXME?)
        @param ignore_dnd: if command results in user interaction, should DnD be ignored?

        """
        # Handle normal notifications
        if isinstance(command, cmd.NotificationCommand):
            cmd_data = command.notification

            for recipient in command.jids:
                jid = JID(recipient)
                jid_text = jid.bare().as_utf8()

                text = cmd_data['text']
                subject = cmd_data.get('subject', '')
                msg_data = command.notification

                if isinstance(command, cmd.NotificationCommandI18n):
                    # Translate&interpolate the message with data
                    gettext_func = self.get_text(jid_text)
                    text, subject = command.translate(gettext_func)
                    msg_data = {'text': text, 'subject': subject,
                                'url_list': cmd_data.get('url_list', [])}

                # Check if contact is DoNotDisturb.
                # If so, queue the message for delayed delivery.
                contact = self.contacts.get(jid_text, '')
                if contact:
                    if command.async and contact.is_dnd() and not ignore_dnd:
                        contact.messages.append(command)
                        return

                self.send_message(jid, msg_data, command.msg_type)

            return

        _ = self.get_text(command.jid)

        # Handle subscribtion management commands
        if isinstance(command, cmd.AddJIDToRosterCommand):
            jid = JID(node_or_jid=command.jid)
            self.ask_for_subscription(jid)

        elif isinstance(command, cmd.RemoveJIDFromRosterCommand):
            jid = JID(node_or_jid=command.jid)
            self.remove_subscription(jid)

        elif isinstance(command, cmd.GetPage) or isinstance(command, cmd.GetPageHTML):
            msg = _(u"""Here's the page "%(pagename)s" that you've requested:\n\n%(data)s""")

            cmd_data = {'text': msg % {'pagename': command.pagename, 'data': command.data}}
            self.send_message(command.jid, cmd_data)

        elif isinstance(command, cmd.GetPageList):
            msg = _("That's the list of pages accesible to you:\n\n%s")
            pagelist = u"\n".join(command.data)

            self.send_message(command.jid, {'text': msg % (pagelist, )})

        elif isinstance(command, cmd.GetPageInfo):
            intro = _("""Following detailed information on page "%(pagename)s" \
is available:""")

            if command.data['author'].startswith("Self:"):
                author = command.data['author'][5:]
            else:
                author = command.data['author']

            datestr = str(command.data['lastModified'])
            date = u"%(year)s-%(month)s-%(day)s at %(time)s" % {
                        'year': datestr[:4],
                        'month': datestr[4:6],
                        'day': datestr[6:8],
                        'time': datestr[9:17],
            }

            msg = _("""Last author: %(author)s
Last modification: %(modification)s
Current version: %(version)s""") % {
             'author': author,
             'modification': date,
             'version': command.data['version'],
            }

            self.send_message(command.jid, {'text': intro % {'pagename': command.pagename}})
            self.send_message(command.jid, {'text': msg})

        elif isinstance(command, cmd.GetUserLanguage):
            if command.jid in self.contacts:
                self.contacts[command.jid].language = command.language

        elif isinstance(command, cmd.Search):
            if command.presentation == u"text":
                if not command.data:
                    msg = _("There are no pages matching your search criteria!")
                    self.send_message(command.jid, {'text': msg})
                    return

                # This hardcoded limitation relies on (mostly correct) assumption that Jabber
                # servers have rather tight traffic limits. Sending more than 25 results is likely
                # to take a second or two - users should not have to wait longer (+search time!).
                elif len(command.data) > 25:
                    msg =  _("There are too many results (%(number)s). Limiting to first 25 entries.") % {'number': str(len(command.data))}
                    self.send_message(command.jid, {'text': msg})
                    command.data = command.data[:25]

                #intro = _("Following pages match your search:\n%(results)s")

                results = [{'description': result[0], 'url': result[2]} for result in command.data]

                data = {'text': _('Following pages match your search criteria:'), 'url_list': results}
                self.send_message(command.jid, data, u"chat")
            else:
                pass
                # TODO: implement data forms here

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

    def send_message(self, jid_text, data, msg_type=u"chat"):
        """Sends a message

        @param jid_text: JID to send the message to
        @param data: dictionary containing notification data
        @param msg_type: message type, as defined in RFC
        @type jid_text: unicode

        """
        use_oob = False
        subject = data.get('subject', '')
        jid = JID(jid_text)

        if data.has_key('url_list') and data['url_list']:
            jid_bare = jid.bare().as_utf8()
            contact = self.contacts.get(jid_bare, None)
            if contact and contact.supports(jid.resource, u'jabber:x:oob'):
                use_oob = True
            else:
                url_strings = ['%s - %s' % (entry['url'], entry['description']) for entry in data['url_list']]
                
                # Insert a newline, so that the list of URLs doesn't start in the same
                # line as the rest of message text
                url_strings.insert(0, '\n')
                data['text'] = data['text'] + '\n'.join(url_strings)
                    
        message = Message(to_jid=jid, body=data['text'], stanza_type=msg_type, subject=subject)
        
        if use_oob:
            oob.add_urls(message, data['url_list'])

        self.get_stream().send(message)

    def send_form(self, jid, form):
        pass

    def send_search_form(self, jid):
        _ = self.get_text(jid)

        # These encode()s may look weird, but due to some pyxmpp oddness we have
        # to provide an utf-8 string instead of unicode. Bug reported, patches submitted...
        form_title = _("Wiki search").encode("utf-8")
        help_form = _("Submit this form to perform a wiki search").encode("utf-8")
        search_type1 = _("Title search")
        search_type2 = _("Full-text search")
        search_label = _("Search type")
        search_label2 = _("Search text")
        forms_warn = _("If you see this, your client probably doesn't support Data Forms.")

        title_search = forms.Option("t", search_type1)
        full_search = forms.Option("f", search_type2)

        form = forms.Form(xmlnode_or_type="form", title=form_title, instructions=help_form)
        form.add_field(name="search_type", options=[title_search, full_search], field_type="list-single", label=search_label)
        form.add_field(name="search", field_type="text-single", label=search_label2)

        message = Message(to_jid=jid, body=forms_warn, subject=_("Wiki search"))
        message.add_content(form)
        self.get_stream().send(message)

    def is_internal(self, command):
        """Check if a given command is internal

        @type command: unicode

        """
        for internal_cmd in self.internal_commands:
            if internal_cmd.lower() == command:
                return True

        return False

    def is_xmlrpc(self, command):
        """Checks if a given commands requires interaction via XMLRPC

        @type command: unicode

        """
        for xmlrpc_cmd in self.xmlrpc_commands:
            if xmlrpc_cmd.lower() == command:
                return True

        return False

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
        if text:
            command = text.split()
            command[0] = command[0].lower()
        else:
            return

        if self.is_internal(command[0]):
            response = self.handle_internal_command(sender, command)
        elif self.is_xmlrpc(command[0]):
            response = self.handle_xmlrpc_command(sender, command)
        else:
            response = self.reply_help(sender)

        if response:
            self.send_message(sender, {'text': response})

    def handle_internal_command(self, sender, command):
        """Handles internal commands, that can be completed by the XMPP bot itself

        @param command: list representing a command
        @param sender: JID of sender
        @type sender: pyxmpp.jid.JID

        """
        _ = self.get_text(sender)

        if command[0] == "ping":
            return "pong"
        elif command[0] == "help":
            if len(command) == 1:
                return self.reply_help(sender)
            else:
                return self.help_on(sender, command[1])
        elif command[0] == "searchform":
            jid = sender.bare().as_utf8()
            resource = sender.resource

            # Assume that outsiders know what they are doing. Clients that don't support
            # data forms should display a warning passed in message <body>.
            if jid not in self.contacts or self.contacts[jid].supports_forms(resource):
                self.send_search_form(sender)
            else:
                msg = {'text': _("This command requires a client supporting Data Forms.")}
                self.send_message(sender, msg, u"")
        else:
            # For unknown command return a generic help message
            return self.reply_help(sender)

    def do_search(self, jid, search_type, presentation, *args):
        """Performs a Wiki search of term

        @param jid: Jabber ID of user performing a search
        @type jid: pyxmpp.jid.JID
        @param term: term to search for
        @type term: unicode
        @param search_type: type of search; either "text" or "title"
        @type search_type: unicode
        @param presentation: how to present the results; "text" or "dataforms"
        @type presentation: unicode

        """
        search = cmd.Search(jid, search_type, presentation=presentation, *args)
        self.from_commands.put_nowait(search)

    def help_on(self, jid, command):
        """Returns a help message on a given topic

        @param command: a command to describe in a help message
        @type command: str or unicode
        @return: a help message

        """
        _ = self.get_text(jid)

        if command == "help":
            return _("""The "help" command prints a short, helpful message \
about a given topic or function.\n\nUsage: help [topic_or_function]""")

        elif command == "ping":
            return _("""The "ping" command returns a "pong" message as soon \
as it's received.""")

        elif command == "searchform":
            return _("""searchform - perform a wiki search using a form""")

        # Here we have to deal with help messages of external (xmlrpc) commands
        else:
            if command in self.xmlrpc_commands:
                classobj = self.xmlrpc_commands[command]
                help_str = _(u"%(command)s - %(description)s\n\nUsage: %(command)s %(params)s")
                return help_str % {'command': command,
                                   'description': classobj.description,
                                   'params': classobj.parameter_list,
                                  }
            else:
                return _("""Unknown command "%s" """) % (command, )

    def handle_xmlrpc_command(self, sender, command):
        """Creates a command object, and puts it the command queue

        @param command: a valid name of available xmlrpc command
        @type command: list representing a command, name and parameters

        """
        _ = self.get_text(sender)
        command_class = self.xmlrpc_commands[command[0]]

        # Add sender's JID to the argument list
        command.insert(1, sender.as_utf8())

        try:
            instance = command_class.__new__(command_class)
            instance.__init__(*command[1:])
            self.from_commands.put_nowait(instance)

        # This happens when user specifies wrong parameters
        except TypeError:
            msg = _("You've specified a wrong parameter list. \
The call should look like:\n\n%(command)s %(params)s")

            return msg % {'command': command[0], 'params': command_class.parameter_list}

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
                    contact.remove_resource(jid.resource)
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
                self.supports(jid, u"jabber:x:data")

            if self.config.verbose:
                self.log.debug(contact)

            # Either way check, if we can deliver queued messages now
            if not contact.is_dnd():
                self.send_queued_messages(contact)

        else:
            self.contacts[bare_jid] = Contact(jid, jid.resource, priority, show)
            self.service_discovery(jid)
            self.get_user_language(bare_jid)
            self.log.debug(self.contacts[bare_jid])

        # Confirm that we've handled this stanza
        return True

    def get_user_language(self, jid):
        """Request user's language setting from the wiki

        @param jid: bare Jabber ID of the user to query for
        @type jid: unicode
        """
        request = cmd.GetUserLanguage(jid)
        self.from_commands.put_nowait(request)

    def service_discovery(self, jid):
        """Ask a client about supported features

        This is not the recommended way of discovering support
        for data forms, but it's easy to implement, so it'll be
        like that for now. The proper way to do this is described
        in XEP-0115 (Entity Capabilities)

        @param jid: FULL (user@host/resource) jabber id to query
        @type jid: unicode

        """
        query = Iq(to_jid=jid, stanza_type="get")
        query.new_query("http://jabber.org/protocol/disco#info")
        self.get_stream().set_response_handlers(query, self.handle_disco_result, None)
        self.get_stream().send(query)


    def handle_disco_result(self, stanza):
        """Handler for <iq> service discovery results

        Works with elements qualified by http://jabber.org/protocol/disco#info ns

        @param stanza: a received result stanza
        """
        payload = stanza.get_query()
        
        supports = payload.xpathEval('//*[@var="jabber:x:data"]')
        if supports:
            jid = stanza.get_from_jid()
            self.contacts[jid.bare().as_utf8()].set_supports(jid.resource, u"jabber:x:data")
            
        supports = payload.xpathEval('//*[@var="jabber:x:oob"]')
        if supports:
            jid = stanza.get_from_jid()
            self.contacts[jid.bare().as_utf8()].set_supports(jid.resource, u"jabber:x:oob")


    def send_queued_messages(self, contact, ignore_dnd=False):
        """Sends messages queued for the contact

        @param contact: a contact whose queued messages are to be sent
        @type contact: jabberbot.xmppbot.Contact
        @param ignore_dnd: should contact's DnD status be ignored?

        """
        for command in contact.messages:
            self.handle_command(command, ignore_dnd)

    def reply_help(self, jid):
        """Constructs a generic help message

        It's sent in response to an uknown message or the "help" command.

        """
        _ = self.get_text(jid)

        msg = _("Hello there! I'm a MoinMoin Notification Bot. Available commands:\
\n\n%(internal)s\n%(xmlrpc)s")
        internal = ", ".join(self.internal_commands)
        xmlrpc = ", ".join(self.xmlrpc_commands.keys())

        return msg % {'internal': internal, 'xmlrpc': xmlrpc}

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
