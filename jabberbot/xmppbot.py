# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import logging, time, Queue
from threading import Thread
from datetime import timedelta

from pyxmpp.cache import Cache
from pyxmpp.cache import CacheItem
from pyxmpp.client import Client
from pyxmpp.jid import JID
from pyxmpp.streamtls import TLSSettings
from pyxmpp.message import Message
from pyxmpp.presence import Presence
from pyxmpp.iq import Iq
import pyxmpp.jabber.dataforms as forms
import libxml2

import jabberbot.commands as cmd
import jabberbot.i18n as i18n
import jabberbot.oob as oob
import jabberbot.capat as capat


class Contact:
    """Abstraction of a roster item / contact

    This class handles some logic related to keeping track of
    contact availability, status, etc."""

    # Default Time To Live of a contact. If there are no registered
    # resources for that period of time, the contact should be removed
    default_ttl = 3600 * 24 # default of one day

    def __init__(self, jid, resource, priority, show, language=None):
        self.jid = jid
        self.resources = {resource: {'show': show, 'priority': priority, 'supports': []}}
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
        self.resources[resource] = {'show': show, 'priority': priority, 'supports': []}
        self.last_online = None

    def set_supports(self, resource, extension):
        """Flag a given resource as supporting a particular extension"""
        self.resources[resource]['supports'].append(extension)

    def supports(self, resource, extension):
        """Check if a given resource supports a particular extension

        If no resource is specified, check the resource with the highest
        priority among currently connected.

        """
        if resource and resource in self.resources:
            return extension in self.resources[resource]['supports']
        else:
            resource = self.max_prio_resource()
            return resource and extension in resource['supports']

    def max_prio_resource(self):
        """Returns the resource (dict) with the highest priority

        @return: highest priority resource or None if contacts is offline
        @rtype: dict or None

        """
        if not self.resources:
            return None

        # Priority can't be lower than -128
        max_prio = -129
        selected = None

        for resource in self.resources.itervalues():
            # TODO: check RFC for behaviour of 2 resources with the same priority
            if resource['priority'] > max_prio:
                max_prio = resource['priority']
                selected = resource

        return selected

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
        max_prio_res = self.max_prio_resource()

        # If there are no resources the contact is offline, not dnd
        if max_prio_res:
            return max_prio_res['show'] == u"dnd"
        else:
            return False

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
        return retval % (self.jid.as_unicode(), res, len(self.messages))


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

        self.config = config
        self.log = logging.getLogger(__name__)
        self.jid = JID(node_or_jid=config.xmpp_node, domain=config.xmpp_server)
        self.tlsconfig = TLSSettings(require = True, verify_peer=False)

        # A dictionary of contact objects, ordered by bare JID
        self.contacts = {}

        # The last time when contacts were checked for expiration, in seconds
        self.last_expiration = time.time()

        # How often should the contacts be checked for expiration, in seconds
        self.contact_check = 600
        self.stopping = False

        self.known_xmlrpc_cmds = [cmd.GetPage, cmd.GetPageHTML, cmd.GetPageList, cmd.GetPageInfo, cmd.Search, cmd.RevertPage]
        self.internal_commands = ["ping", "help", "searchform"]

        self.xmlrpc_commands = {}
        for command, name in [(command, command.__name__) for command in self.known_xmlrpc_cmds]:
            self.xmlrpc_commands[name.lower()] = command

        Client.__init__(self, self.jid, config.xmpp_password, config.xmpp_server, tls_settings=self.tlsconfig)

        # Setup message handlers

        self._msg_handlers = {cmd.NotificationCommand: self._handle_notification,
                              cmd.NotificationCommandI18n: self._handle_notification,
                              cmd.AddJIDToRosterCommand: self._handle_add_contact,
                              cmd.RemoveJIDFromRosterCommand: self._handle_remove_contact,
                              cmd.GetPage: self._handle_get_page,
                              cmd.GetPageHTML: self._handle_get_page,
                              cmd.GetPageList: self._handle_get_page_list,
                              cmd.GetPageInfo: self._handle_get_page_info,
                              cmd.GetUserLanguage: self._handle_get_language,
                              cmd.Search: self._handle_search}

        # cache for service discovery results ( (ver, algo) : Capabilities = libxml2.xmlNode)
        self.disco_cache = Cache(max_items=config.disco_cache_size, default_purge_period=0)

        # dictionary of jids waiting for service discovery results
        # ( (ver, algo) : (timeout=datetime.timedelta, [list_of_jids=pyxmpp.jid]) )
        self.disco_wait = {}

        # temporary dictionary ( pyxmpp.jid:  (ver, algo) )
        self.disco_temp = {}

    def run(self):
        """Start the bot - enter the event loop"""

        self.log.info("Starting the jabber bot.")
        self.connect()
        self.loop()

    def stop(self):
        """Stop the thread"""
        self.stopping = True

    def loop(self, timeout=1):
        """Main event loop - stream and command handling"""

        while True:
            if self.stopping:
                break

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

        self.disco_cache.tick()
        self.check_disco_delays()

    def session_started(self):
        """Handle session started event.
        Requests the user's roster and sends the initial presence with
        a <c> child as described in XEP-0115 (Entity Capabilities)

        """
        self.request_roster()
        pres = capat.create_presence(self.jid)
        self.stream.set_iq_get_handler("query", "http://jabber.org/protocol/disco#info", self.handle_disco_query)
        self.stream.send(pres)

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
            jid = JID(jid).bare().as_unicode()
        else:
            jid = jid.bare().as_unicode()

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

    def handle_command(self, command, ignore_dnd=False):
        """Excecutes commands from other components

        @param command: a command to execute
        @type command: any class defined in commands.py (FIXME?)
        @param ignore_dnd: if command results in user interaction, should DnD be ignored?

        """

        cmd_cls = command.__class__

        try:
            handler = self._msg_handlers[cmd_cls]
        except KeyError:
            self.log.debug("No such command: " + cmd_cls.__name__)
            return

        # NOTE: handler is a method, so it takes self as a hidden arg
        handler(command, ignore_dnd)

    def handle_changed_action(self, cmd_data, jid, contact):
        """Handles a notification command with 'page_changed' action

        @param cmd_data: notification command data
        @param jid: jid to send the notification to
        @param contact: a roster contact
        @type cmd_data: dict
        @type jid: pyxmpp.jid.JID
        @type contact: Contact

        """
        if contact and contact.supports(jid.resource, u"jabber:x:data"):
            self.send_change_form(jid.as_unicode(), cmd_data)
            return
        else:
            self.send_change_text(jid.as_unicode(), cmd_data)

    def handle_deleted_action(self, cmd_data, jid, contact):
        """Handles a notification cmd_data with 'page_deleted' action

        @param cmd_data: notification cmd_data
        @param jid: jid to send the notification to
        @param contact: a roster contact
        @type cmd_data: dict
        @type jid: pyxmpp.jid.JID
        @type contact: Contact

        """
        if contact and contact.supports(jid.resource, u"jabber:x:data"):
            self.send_deleted_form(jid.as_unicode(), cmd_data)
            return
        else:
            self.send_deleted_text(jid.as_unicode(), cmd_data)

    def handle_attached_action(self, cmd_data, jid, contact):
        """Handles a notification cmd_data with 'file_attached' action

        @param cmd_data: notification cmd_data
        @param jid: jid to send the notification to
        @param contact: a roster contact
        @type cmd_data: dict
        @type jid: pyxmpp.jid.JID
        @type contact: Contact

        """
        if contact and contact.supports(jid.resource, u"jabber:x:data"):
            self.send_attached_form(jid.as_unicode(), cmd_data)
            return
        else:
            self.send_attached_text(jid.as_unicode(), cmd_data)

    def handle_renamed_action(self, cmd_data, jid, contact):
        """Handles a notification cmd_data with 'page_renamed' action

        @param cmd_data: notification cmd_data
        @param jid: jid to send the notification to
        @param contact: a roster contact
        @type cmd_data: dict
        @type jid: pyxmpp.jid.JID
        @type contact: Contact

        """
        if contact and contact.supports(jid.resource, u"jabber:x:data"):
            self.send_renamed_form(jid.as_unicode(), cmd_data)
            return
        else:
            self.send_renamed_text(jid.as_unicode(), cmd_data)

    def handle_user_created_action(self, cmd_data, jid, contact):
        """Handles a notification cmd_data with 'user_created' action

        @param cmd_data: notification cmd_data
        @param jid: jid to send the notification to
        @param contact: a roster contact
        @type cmd_data: dict
        @type jid: pyxmpp.jid.JID
        @type contact: Contact

        """
        # TODO: send as form if user-client supports it
        self.send_user_created_text(jid.as_unicode(), cmd_data)

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
            jid_bare = jid.bare().as_unicode()
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

    def send_form(self, jid, form, subject, url_list=[]):
        """Send a data form

        @param jid: jid to send the form to (full)
        @param form: the form to send
        @param subject: subject of the message
        @param url_list: list of urls to use with OOB
        @type jid: unicode
        @type form: pyxmpp.jabber.dataforms.Form
        @type subject: unicode
        @type url_list: list

        """
        if not isinstance(form, forms.Form):
            raise ValueError("The 'form' argument must be of type pyxmpp.jabber.dataforms.Form!")

        _ = self.get_text(JID(jid).bare().as_unicode())

        message = Message(to_jid=jid, subject=subject)
        message.add_content(form)

        if url_list:
            oob.add_urls(message, url_list)

        self.get_stream().send(message)

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
        case_label = _("Case-sensitive search")
        regexp_label = _("Treat terms as regular expressions")
        forms_warn = _("If you see this, your client probably doesn't support Data Forms.")

        title_search = forms.Option("t", search_type1)
        full_search = forms.Option("f", search_type2)

        form = forms.Form(xmlnode_or_type="form", title=form_title, instructions=help_form)
        form.add_field(name="action", field_type="hidden", value="search")
        form.add_field(name="case", field_type="boolean", label=case_label)
        form.add_field(name="regexp", field_type="boolean", label=regexp_label)
        form.add_field(name="search_type", options=[title_search, full_search], field_type="list-single", label=search_label)
        form.add_field(name="search", field_type="text-single", label=search_label2)

        self.send_form(jid, form, _("Wiki search"))

    def send_change_form(self, jid, msg_data):
        """Sends a page change notification using Data Forms

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)

        form_title = _("Page changed notification").encode("utf-8")
        instructions = _("Submit this form with a specified action to continue.").encode("utf-8")
        action_label = _("What to do next")

        action1 = _("Do nothing")
        action2 = _("Revert change")
        action3 = _("View page info")
        action4 = _("Perform a search")

        do_nothing = forms.Option("n", action1)
        revert = forms.Option("r", action2)
        view_info = forms.Option("v", action3)
        search = forms.Option("s", action4)

        form = forms.Form(xmlnode_or_type="form", title=form_title, instructions=instructions)
        form.add_field(name='revision', field_type='hidden', value=msg_data['revision'])
        form.add_field(name='page_name', field_type='hidden', value=msg_data['page_name'])
        form.add_field(name='editor', field_type='text-single', value=msg_data['editor'], label=_("Editor"))
        form.add_field(name='comment', field_type='text-single', value=msg_data.get('comment', ''), label=_("Comment"))

        # Add lines of text as separate values, as recommended in XEP
        diff_lines = msg_data['diff'].split('\n')
        form.add_field(name="diff", field_type="text-multi", values=diff_lines, label=("Diff"))

        full_jid = JID(jid)
        bare_jid = full_jid.bare().as_unicode()
        resource = full_jid.resource

        # Add URLs as OOB data if it's supported and as separate fields otherwise
        if bare_jid in self.contacts and self.contacts[bare_jid].supports(resource, u'jabber:x:oob'):
            url_list = msg_data['url_list']
        else:
            url_list = []

            for number, url in enumerate(msg_data['url_list']):
                field_name = "url%d" % (number, )
                form.add_field(name=field_name, field_type="text-single", value=url["url"], label=url["description"])

        # Selection of a following action
        form.add_field(name="options", field_type="list-single", options=[do_nothing, revert, view_info, search], label=action_label)

        self.send_form(jid, form, _("Page change notification"), url_list)

    def send_change_text(self, jid, msg_data):
        """Sends a simple, text page change notification

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)
        separator = '-' * 78
        urls_text = '\n'.join(["%s - %s" % (url["description"], url["url"]) for url in msg_data['url_list']])
        message = _("%(preamble)s\nComment: %(comment)s\n%(separator)s\n%(diff)s\n%(separator)s\n%(links)s") % {
                    'preamble': msg_data['text'],
                    'separator': separator,
                    'diff': msg_data['diff'],
                    'comment': msg_data.get('comment', _('no comment')),
                    'links': urls_text,
                  }

        data = {'text': message, 'subject': msg_data.get('subject', '')}
        self.send_message(jid, data, u"normal")

    def send_deleted_form(self, jid, msg_data):
        """Sends a page deleted notification using Data Forms

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)

        form_title = _("Page deletion notification").encode("utf-8")
        instructions = _("Submit this form with a specified action to continue.").encode("utf-8")
        action_label = _("What to do next")

        action1 = _("Do nothing")
        action2 = _("Perform a search")

        do_nothing = forms.Option("n", action1)
        search = forms.Option("s", action2)

        form = forms.Form(xmlnode_or_type="form", title=form_title, instructions=instructions)
        form.add_field(name='editor', field_type='text-single', value=msg_data['editor'], label=_("Editor"))
        form.add_field(name='comment', field_type='text-single', value=msg_data.get('comment', ''), label=_("Comment"))

        full_jid = JID(jid)
        bare_jid = full_jid.bare().as_unicode()
        resource = full_jid.resource

        # Add URLs as OOB data if it's supported and as separate fields otherwise
        if bare_jid in self.contacts and self.contacts[bare_jid].supports(resource, u'jabber:x:oob'):
            url_list = msg_data['url_list']
        else:
            url_list = []

            for number, url in enumerate(msg_data['url_list']):
                field_name = "url%d" % (number, )
                form.add_field(name=field_name, field_type="text-single", value=url["url"], label=url["description"])

        # Selection of a following action
        form.add_field(name="options", field_type="list-single", options=[do_nothing, search], label=action_label)

        self.send_form(jid, form, _("Page deletion notification"), url_list)

    def send_deleted_text(self, jid, msg_data):
        """Sends a simple, text page deletion notification

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)
        separator = '-' * 78
        urls_text = '\n'.join(["%s - %s" % (url["description"], url["url"]) for url in msg_data['url_list']])
        message = _("%(preamble)s\nComment: %(comment)s\n%(separator)s\n%(links)s") % {
                    'preamble': msg_data['text'],
                    'separator': separator,
                    'comment': msg_data.get('comment', _('no comment')),
                    'links': urls_text,
                  }

        data = {'text': message, 'subject': msg_data.get('subject', '')}
        self.send_message(jid, data, u"normal")

    def send_attached_form(self, jid, msg_data):
        """Sends a new attachment notification using Data Forms

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)

        form_title = _("File attached notification").encode("utf-8")
        instructions = _("Submit this form with a specified action to continue.").encode("utf-8")
        action_label = _("What to do next")

        action1 = _("Do nothing")
        action2 = _("View page info")
        action3 = _("Perform a search")

        do_nothing = forms.Option("n", action1)
        view_info = forms.Option("v", action2)
        search = forms.Option("s", action3)

        form = forms.Form(xmlnode_or_type="form", title=form_title, instructions=instructions)
        form.add_field(name='page_name', field_type='hidden', value=msg_data['page_name'])
        form.add_field(name='editor', field_type='text-single', value=msg_data['editor'], label=_("Editor"))
        form.add_field(name='page', field_type='text-single', value=msg_data['page_name'], label=_("Page name"))
        form.add_field(name='name', field_type='text-single', value=msg_data['attach_name'], label=_("File name"))
        form.add_field(name='size', field_type='text-single', value=msg_data['attach_size'], label=_("File size"))

        full_jid = JID(jid)
        bare_jid = full_jid.bare().as_unicode()
        resource = full_jid.resource

        # Add URLs as OOB data if it's supported and as separate fields otherwise
        if bare_jid in self.contacts and self.contacts[bare_jid].supports(resource, u'jabber:x:oob'):
            url_list = msg_data['url_list']
        else:
            url_list = []

            for number, url in enumerate(msg_data['url_list']):
                field_name = "url%d" % (number, )
                form.add_field(name=field_name, field_type="text-single", value=url["url"], label=url["description"])

        # Selection of a following action
        form.add_field(name="options", field_type="list-single", options=[do_nothing, view_info, search], label=action_label)

        self.send_form(jid, form, _("File attached notification"), url_list)

    def send_attached_text(self, jid, msg_data):
        """Sends a simple, text page deletion notification

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)
        separator = '-' * 78
        urls_text = '\n'.join(["%s - %s" % (url["description"], url["url"]) for url in msg_data['url_list']])
        message = _("%(preamble)s\n%(separator)s\n%(links)s") % {
                    'preamble': msg_data['text'],
                    'separator': separator,
                    'links': urls_text,
                  }

        data = {'text': message, 'subject': msg_data['subject']}
        self.send_message(jid, data, u"normal")

    def send_renamed_form(self, jid, msg_data):
        """Sends a page rename notification using Data Forms

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)

        form_title = _("Page rename notification").encode("utf-8")
        instructions = _("Submit this form with a specified action to continue.").encode("utf-8")
        action_label = _("What to do next")

        action1 = _("Do nothing")
        action2 = _("Revert change")
        action3 = _("View page info")
        action4 = _("Perform a search")

        do_nothing = forms.Option("n", action1)
        revert = forms.Option("r", action2)
        view_info = forms.Option("v", action3)
        search = forms.Option("s", action4)

        form = forms.Form(xmlnode_or_type="form", title=form_title, instructions=instructions)
        form.add_field(name='revision', field_type='hidden', value=msg_data['revision'])
        form.add_field(name='page_name', field_type='hidden', value=msg_data['page_name'])
        form.add_field(name='editor', field_type='text-single', value=msg_data['editor'], label=_("Editor"))
        form.add_field(name='comment', field_type='text-single', value=msg_data.get('comment', ''), label=_("Comment"))
        form.add_field(name='old', field_type='text-single', value=msg_data['old_name'], label=_("Old name"))
        form.add_field(name='new', field_type='text-single', value=msg_data['page_name'], label=_("New name"))

        full_jid = JID(jid)
        bare_jid = full_jid.bare().as_unicode()
        resource = full_jid.resource

        # Add URLs as OOB data if it's supported and as separate fields otherwise
        if bare_jid in self.contacts and self.contacts[bare_jid].supports(resource, u'jabber:x:oob'):
            url_list = msg_data['url_list']
        else:
            url_list = []

            for number, url in enumerate(msg_data['url_list']):
                field_name = "url%d" % (number, )
                form.add_field(name=field_name, field_type="text-single", value=url["url"], label=url["description"])

        # Selection of a following action
        form.add_field(name="options", field_type="list-single", options=[do_nothing, revert, view_info, search], label=action_label)

        self.send_form(jid, form, _("Page rename notification"), url_list)

    def send_renamed_text(self, jid, msg_data):
        """Sends a simple, text page rename notification

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)
        separator = '-' * 78
        urls_text = '\n'.join(["%s - %s" % (url["description"], url["url"]) for url in msg_data['url_list']])
        message = _("%(preamble)s\nComment: %(comment)s\n%(separator)s\n%(links)s") % {
                    'preamble': msg_data['text'],
                    'separator': separator,
                    'comment': msg_data.get('comment', _('no comment')),
                    'links': urls_text,
                  }

        data = {'text': message, 'subject': msg_data['subject']}
        self.send_message(jid, data, u"normal")

    def send_user_created_text(self, jid, msg_data):
        """Sends a simple, text page user-created-notification

        @param jid: a Jabber ID to send the notification to
        @type jid: unicode
        @param msg_data: dictionary with notification data
        @type msg_data: dict

        """
        _ = self.get_text(jid)
        message = _("%(text)s") % {'text': msg_data['text']}

        data = {'text': message, 'subject': msg_data['subject']}
        self.send_message(jid, data, u"normal")

    def handle_page_info(self, command):
        """Handles GetPageInfo commands

        @param command: a command instance
        @type command: jabberbot.commands.GetPageInfo

        """
        # Process command data first so it can be directly usable
        if command.data['author'].startswith("Self:"):
            command.data['author'] = command.data['author'][5:]

        datestr = str(command.data['lastModified'])
        command.data['lastModified'] = u"%(year)s-%(month)s-%(day)s at %(time)s" % {
                    'year': datestr[:4],
                    'month': datestr[4:6],
                    'day': datestr[6:8],
                    'time': datestr[9:17],
        }

        if command.presentation == u"text":
            self.send_pageinfo_text(command)
        elif command.presentation == u"dataforms":
            self.send_pageinfo_form(command)

        else:
            raise ValueError("presentation value '%s' is not supported!" % (command.presentation, ))

    def send_pageinfo_text(self, command):
        """Sends detailed page info with plain text

        @param command: command with detailed data
        @type command: jabberbot.command.GetPageInfo

        """
        _ = self.get_text(command.jid)

        intro = _("""Following detailed information on page "%(pagename)s" \
is available:""")

        msg = _("""Last author: %(author)s
Last modification: %(modification)s
Current version: %(version)s""") % {
         'author': command.data['author'],
         'modification': command.data['lastModified'],
         'version': command.data['version'],
        }

        self.send_message(command.jid, {'text': intro % {'pagename': command.pagename}})
        self.send_message(command.jid, {'text': msg})

    def send_pageinfo_form(self, command):
        """Sends page info using Data Forms


        """
        _ = self.get_text(command.jid)
        data = command.data

        form_title = _("Detailed page information").encode("utf-8")
        instructions = _("Submit this form with a specified action to continue.").encode("utf-8")
        action_label = _("What to do next")

        action1 = _("Do nothing")
        action2 = _("Get page contents")
        action3 = _("Get page contents (HTML)")
        action4 = _("Perform a search")

        do_nothing = forms.Option("n", action1)
        get_content = forms.Option("c", action2)
        get_content_html = forms.Option("h", action3)
        search = forms.Option("s", action4)

        form = forms.Form(xmlnode_or_type="form", title=form_title, instructions=instructions)
        form.add_field(name='pagename', field_type='text-single', value=command.pagename, label=_("Page name"))
        form.add_field(name="changed", field_type='text-single', value=data['lastModified'], label=_("Last changed"))
        form.add_field(name='editor', field_type='text-single', value=data['author'], label=_("Last editor"))
        form.add_field(name='version', field_type='text-single', value=data['version'], label=_("Current version"))

#        full_jid = JID(jid)
#        bare_jid = full_jid.bare().as_unicode()
#        resource = full_jid.resource

        # Add URLs as OOB data if it's supported and as separate fields otherwise
#        if bare_jid in self.contacts and self.contacts[bare_jid].supports(resource, u'jabber:x:oob'):
#            url_list = msg_data['url_list']
#        else:
#            url_list = []
#
#            for number, url in enumerate(msg_data['url_list']):
#                field_name = "url%d" % (number, )
#                form.add_field(name=field_name, field_type="text-single", value=url["url"], label=url["description"])

        # Selection of a following action
        form.add_field(name="options", field_type="list-single", options=[do_nothing, get_content, get_content_html, search], label=action_label)

        self.send_form(command.jid, form, _("Detailed page information"))

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

    def contains_form(self, message):
        """Checks if passed message stanza contains a submitted form and parses it

        @param message: message stanza
        @type message: pyxmpp.message.Message
        @return: xml node with form data if found, or None

        """
        if not isinstance(message, Message):
            raise ValueError("The 'message' parameter must be of type pyxmpp.message.Message!")

        payload = message.get_node()
        form = message.xpath_eval('/ns:message/data:x', {'data': 'jabber:x:data'})

        if form:
            return form[0]
        else:
            return None

    def handle_form(self, jid, form_node):
        """Handles a submitted data form

        @param jid: jid that submitted the form (full jid)
        @type jid: pyxmpp.jid.JID
        @param form_node: a xml node with data form
        @type form_node: libxml2.xmlNode

        """
        if not isinstance(form_node, libxml2.xmlNode):
            raise ValueError("The 'form' parameter must be of type libxml2.xmlNode!")

        if not isinstance(jid, JID):
            raise ValueError("The 'jid' parameter must be of type jid!")

        _ = self.get_text(jid.bare().as_unicode())

        form = forms.Form(form_node)

        if form.type != u"submit":
            return

        if "action" in form:
            action = form["action"].value
            if action == u"search":
                self.handle_search_form(jid, form)
            else:
                data = {'text': _('The form you submitted was invalid!'), 'subject': _('Invalid data')}
                self.send_message(jid.as_unicode(), data, u"normal")
        elif "options" in form:
            option = form["options"].value

            # View page info
            if option == "v":
                command = cmd.GetPageInfo(jid.as_unicode(), form["page_name"].value, presentation="dataforms")
                self.from_commands.put_nowait(command)

            # Perform an another search
            elif option == "s":
                self.handle_internal_command(jid, ["searchform"])

            # Revert a change
            elif option == "r":
                revision = int(form["revision"].value)

                # We can't really revert creation of a page, right?
                if revision == 1:
                    return

                self.handle_xmlrpc_command(jid, ["revertpage", form["page_name"].value, "%d" % (revision - 1, )])

    def handle_search_form(self, jid, form):
        """Handles a search form

        @param jid: jid that submitted the form
        @type jid: pyxmpp.jid.JID
        @param form: a form object
        @type form_node: pyxmpp.jabber.dataforms.Form

        """
        required_fields = ["case", "regexp", "search_type", "search"]
        jid_text = jid.bare().as_unicode()
        _ = self.get_text(jid_text)

        for field in required_fields:
            if field not in form:
                data = {'text': _('The form you submitted was invalid!'), 'subject': _('Invalid data')}
                self.send_message(jid.as_unicode(), data, u"normal")

        case_sensitive = form['case'].value
        regexp_terms = form['regexp'].value
        if form['search_type'].value == 't':
            search_type = 'title'
        else:
            search_type = 'text'

        command = cmd.Search(jid.as_unicode(), search_type, form["search"].value, case=form['case'].value,
                             regexp=form['regexp'].value, presentation='dataforms')
        self.from_commands.put_nowait(command)

    def handle_message(self, message):
        """Handles incoming messages

        @param message: a message stanza to parse
        @type message: pyxmpp.message.Message

        """
        if self.config.verbose:
            msg = "Message from %s." % (message.get_from_jid().as_unicode(), )
            self.log.debug(msg)

        form = self.contains_form(message)
        if form:
            self.handle_form(message.get_from_jid(), form)
            return

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
            jid = sender.bare().as_unicode()
            resource = sender.resource

            # Assume that outsiders know what they are doing. Clients that don't support
            # data forms should display a warning passed in message <body>.
            if jid not in self.contacts or self.contacts[jid].supports(resource, u"jabber:x:data"):
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
        command.insert(1, sender.as_unicode())

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
        bare_jid = jid.bare().as_unicode()

        # If we get presence, this contact should already be known
        if bare_jid in self.contacts:
            contact = self.contacts[bare_jid]

            if self.config.verbose:
                self.log.debug("%s, going OFFLINE." % contact)

            # check if we are waiting for disco#info from this jid
            self.check_if_waiting(jid)
            del self.disco_temp[jid]

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
        bare_jid = jid.bare().as_unicode()

        if bare_jid in self.contacts:
            contact = self.contacts[bare_jid]

            # The resource is already known, so update it
            if contact.uses_resource(jid.resource):
                contact.set_show(jid.resource, show)

            # Unknown resource, add it to the list
            else:
                contact.add_resource(jid.resource, show, priority)

                # Discover capabilities of the newly connected client
                self.service_discovery(jid, presence)

            if self.config.verbose:
                self.log.debug(contact)

            # Either way check, if we can deliver queued messages now
            if not contact.is_dnd():
                self.send_queued_messages(contact)

        else:
            self.contacts[bare_jid] = Contact(jid, jid.resource, priority, show)
            self.service_discovery(jid, presence)
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

    def handle_disco_query(self, stanza):
        """Handler for <Iq /> service discovery query

        @param stanza: received query stanza (pyxmpp.iq.Iq)
        """
        response = capat.create_response(stanza)
        self.get_stream().send(response)

    def service_discovery(self, jid, presence):
        """General handler for XEP-0115 (Entity Capabilities)

        @param jid: whose capabilities to discover (pyxmpp.jid.JID)
        @param presence: received presence stanza (pyxmpp.presence.Presence)
        """
        ver_algo = self.check_presence(presence)
        self.disco_temp[jid] = ver_algo

        if ver_algo is None:
            # legacy client - send disco#info query
            self.send_disco_query(jid)
        else:
            # check if we have this (ver,algo) already cached
            cache_item = self.disco_cache.get_item(ver_algo, state='stale')

            if cache_item is None:
                # add to disco_wait
                self.add_to_disco_wait(ver_algo, jid)
            else:
                # use cached capabilities
                self.log.debug(u"%s: using cached capabilities." % jid.as_unicode())
                payload = cache_item.value
                self.set_support(jid, payload)

    def check_presence(self, presence):
        """Search received presence for a <c> child with 'ver' and 'algo' attributes
        return (ver, algo) or None if no 'ver' found.
        (no 'algo' attribute defaults to 'sha-1', as described in XEP-0115)

        @param presence: received presence stanza (pyxmpp.presence.Presence)
        @return type: tuple of (str, str) or None
        """
        # TODO: <c> could be found directly using more appropriate xpath
        tags = presence.xpath_eval('child::*')
        for tag in tags:
            if tag.name == 'c':
                ver = tag.xpathEval('@ver')
                algo = tag.xpathEval('@algo')
                if ver:
                    if algo:
                        ver_algo = (ver[0].children.content, algo[0].children.content)
                    else:
                        # no algo attribute defaults to 'sha-1'
                        ver_algo = (ver[0].children.content, 'sha-1')

                    return ver_algo
                else:
                    #self.log.debug(u"%s: presence with <c> but without 'ver' attribute." % jid.as_unicode())
                    return None
                break
        else:
            #self.log.debug(u"%s: presence without a <c> tag." % jid.as_unicode())
            return None

    def send_disco_query(self, jid):
        """Sends disco#info query to a given jid

        @type jid: pyxmpp.jid.JID
        """
        query = Iq(to_jid=jid, stanza_type="get")
        query.new_query("http://jabber.org/protocol/disco#info")
        self.get_stream().set_response_handlers(query, self.handle_disco_result, None)
        self.get_stream().send(query)

    def add_to_disco_wait(self, ver_algo, jid):
        """Adds given jid to the list of contacts waiting for service
        discovery results.

        @param ver_algo: 'ver' and 'algo' attributes of the given jid
        @type ver_algo: tuple of (str, str)
        @type jid: pyxmpp.jid.JID
        """
        if ver_algo in self.disco_wait:
            # query already sent, add to the end of waiting list
            self.disco_wait[ver_algo][1].append(jid)
        else:
            # send a query and create a new entry
            self.send_disco_query(jid)
            timeout = time.time() + self.config.disco_answering_timeout
            self.disco_wait[ver_algo] = (timeout, [jid])

    def handle_disco_result(self, stanza):
        """Handler for <iq> service discovery results
        check if contact is still available and if 'ver' matches the capabilities' hash

        @param stanza: a received result stanza (pyxmpp.iq.Iq)
        """
        jid = stanza.get_from_jid()
        bare_jid = jid.bare().as_unicode()
        payload = stanza.get_query()

        if bare_jid in self.contacts:
            ver_algo = self.disco_temp[jid]

            if ver_algo is not None:
                ver, algo = ver_algo
                payload_hash = capat.hash_iq(stanza, algo)

                if payload_hash == ver:
                    # we can trust this 'ver' string
                    self.disco_result_right(ver_algo, payload)
                else:
                    self.log.debug(u"%s: 'ver' and hash do not match! (legacy client?)" % jid.as_unicode())
                    self.disco_result_wrong(ver_algo)

            self.set_support(jid, payload)

        else:
            self.log.debug(u"%s is unavailable but sends service discovery response." % jid.as_unicode())
            # such situation is handled by check_if_waiting

    def disco_result_right(self, ver_algo, payload):
        """We received a correct service discovery response so we can safely cache it
        for future use and apply to every waiting contact from the list (first one is already done)

        @param ver_algo: 'ver' and 'algo' attributes matching received capabilities
        @param payload: received capabilities
        @type ver_algo: tuple of (str, str)
        @type payload: libxml2.xmlNode
        """
        delta = timedelta(0)
        cache_item = CacheItem(ver_algo, payload, delta, delta, delta)
        self.disco_cache.add_item(cache_item)

        timeout, jid_list = self.disco_wait[ver_algo]
        for jid in jid_list[1:]:
            if jid.bare().as_unicode() in self.contacts:
                self.set_support(jid, payload)
        del self.disco_wait[ver_algo]

    def disco_result_wrong(self, ver_algo):
        """First jid from the list returned wrong response
        if it is possible try to ask the second one

        @param ver_algo: 'ver' and 'algo' attributes for which we received an inappropriate response
        @type ver_algo: tuple of (str, str)
        """
        timeout, jid_list = self.disco_wait[ver_algo]
        jid_list = jid_list[1:]
        if jid_list:
            self.send_disco_query(jid_list[0])
            timeout = time.time() + self.config.disco_answering_timeout
            self.disco_wait[ver_algo] = (timeout, jid_list)
        else:
            del self.disco_wait[ver_algo]

    def check_disco_delays(self):
        """Called when idle to check if some contacts haven't answered in allowed time"""
        for item in self.disco_wait:
            timeout, jid_list = self.disco_wait[item]
            if timeout < time.time():
                self.disco_result_wrong(item)

    def check_if_waiting(self, jid):
        """Check if we were waiting for disco#info reply from client that
        has just become unavailable. If so, ask next candidate.

        @param jid: jid that has just gone unavailable
        @type jid: pyxmpp.jid.JID
        """
        ver_algo = self.disco_temp[jid]
        if ver_algo in self.disco_wait:
            timeout, jid_list = self.disco_wait[ver_algo]
            if jid_list:
                if jid == jid_list[0]:
                    self.disco_result_wrong(ver_algo)
            else:
                # this should never happen
                self.log.debug(u"disco_wait: keeping empty entry at (%s, %s) !" % ver_algo)

    def set_support(self, jid, payload):
        """Searches service discovery results for support for
        Out Of Band Data (XEP-066) and Data Forms (XEP-004)
        and applies it to newly created Contact.

        @param jid: client's jabber ID (pyxmpp.jid.JID)
        @param payload: client's capabilities (libxml2.xmlNode)
        """
        supports = payload.xpathEval('//*[@var="jabber:x:oob"]')
        if supports:
            self.contacts[jid.bare().as_unicode()].set_supports(jid.resource, u"jabber:x:oob")

        supports = payload.xpathEval('//*[@var="jabber:x:data"]')
        if supports:
            self.contacts[jid.bare().as_unicode()].set_supports(jid.resource, u"jabber:x:data")

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

    # Message handlers

    def _handle_notification(self, command, ignore_dnd):
        cmd_data = command.notification
        original_text = cmd_data.get('text', '')
        original_subject = cmd_data.get('subject', '')

        for recipient in command.jids:
            jid = JID(recipient)
            jid_text = jid.bare().as_unicode()

            if isinstance(command, cmd.NotificationCommandI18n):
                # Translate&interpolate the message with data
                gettext_func = self.get_text(jid_text)
                text, subject = command.translate(gettext_func)
                cmd_data['text'] = text
                cmd_data['subject'] = subject
            else:
                cmd_data['text'] = original_text
                cmd_data['subject'] = original_subject

            # Check if contact is DoNotDisturb.
            # If so, queue the message for delayed delivery.
            contact = self.contacts.get(jid_text, '')
            if contact:
                if command.async and contact.is_dnd() and not ignore_dnd:
                    contact.messages.append(command)
                    return

            action = cmd_data.get('action', '')
            if action == u'page_changed':
                self.handle_changed_action(cmd_data, jid, contact)
            elif action == u'page_deleted':
                self.handle_deleted_action(cmd_data, jid, contact)
            elif action == u'file_attached':
                self.handle_attached_action(cmd_data, jid, contact)
            elif action == u'page_renamed':
                self.handle_renamed_action(cmd_data, jid, contact)
            elif action == u'user_created':
                self.handle_user_created_action(cmd_data, jid, contact)
            else:
                self.send_message(jid, cmd_data, command.msg_type)

    def _handle_search(self, command, ignore_dnd):
        warnings = []
        _ = self.get_text(command.jid)

        if not command.data:
            warnings.append(_("There are no pages matching your search criteria!"))

        # This hardcoded limitation relies on (mostly correct) assumption that Jabber
        # servers have rather tight traffic limits. Sending more than 25 results is likely
        # to take a second or two - users should not have to wait longer (+search time!).
        elif len(command.data) > 25:
            warnings.append(_("There are too many results (%(number)s). Limiting to first 25 entries.") % {'number': str(len(command.data))})
            command.data = command.data[:25]

        results = [{'description': result[0], 'url': result[2]} for result in command.data]

        if command.presentation == u"text":
            for warning in warnings:
                self.send_message(command.jid, {'text': warning})

            if not results:
                return

            data = {'text': _('Following pages match your search criteria:'), 'url_list': results}
            self.send_message(command.jid, data, u"chat")
        else:
            form_title = _("Search results").encode("utf-8")
            help_form = _("Submit this form to perform a wiki search").encode("utf-8")
            form = forms.Form(xmlnode_or_type="result", title=form_title, instructions=help_form)

            action_label = _("What to do next")
            do_nothing = forms.Option("n", _("Do nothing"))
            search_again = forms.Option("s", _("Search again"))

            for no, warning in enumerate(warnings):
                form.add_field(name="warning", field_type="fixed", value=warning)

            for no, result in enumerate(results):
                field_name = "url%d" % (no, )
                form.add_field(name=field_name, value=unicode(result["url"]), label=result["description"].encode("utf-8"), field_type="text-single")

            # Selection of a following action
            form.add_field(name="options", field_type="list-single", options=[do_nothing, search_again], label=action_label)

            self.send_form(command.jid, form, _("Search results"))

    def _handle_add_contact(self, command, ignore_dnd):
        jid = JID(node_or_jid = command.jid)
        self.ask_for_subscription(jid)

    def _handle_remove_contact(self, command, ignore_dnd):
        jid = JID(node_or_jid = command.jid)
        self.remove_subscription(jid)

    def _handle_get_page(self, command, ignore_dnd):
        _ = self.get_text(command.jid)
        msg = _(u"""Here's the page "%(pagename)s" that you've requested:\n\n%(data)s""")

        cmd_data = {'text': msg % {'pagename': command.pagename, 'data': command.data}}
        self.send_message(command.jid, cmd_data)

    def _handle_get_page_list(self, command, ignore_dnd):
        _ = self.get_text(command.jid)
        msg = _("That's the list of pages accesible to you:\n\n%s")
        pagelist = u"\n".join(command.data)

        self.send_message(command.jid, {'text': msg % (pagelist, )})

    def _handle_get_page_info(self, command, ignore_dnd):
        self.handle_page_info(command)

    def _handle_get_language(self, command, ignore_dnd):
        if command.jid in self.contacts:
            self.contacts[command.jid].language = command.language
