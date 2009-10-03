# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a xmlrpc server and client for the notification bot

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import logging, xmlrpclib, Queue
from SimpleXMLRPCServer import SimpleXMLRPCServer
from threading import Thread

import jabberbot.commands as cmd


class ConfigurationError(Exception):

    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


def _xmlrpc_decorator(function):
    """A decorator function, which adds some maintenance code

    This function takes care of preparing a MultiCall object and
    an authentication token, and deleting them at the end.

    """
    def wrapped_func(self, command):
        # Dummy function, so that the string appears in a .po file
        _ = lambda x: x

        self.token = None
        self.multicall = xmlrpclib.MultiCall(self.connection)
        jid = command.jid
        if type(jid) is not list:
            jid = [jid]

        try:
            try:
                self.get_auth_token(command.jid)
                if self.token:
                    self.multicall.applyAuthToken(self.token)

                function(self, command)
                self.commands_out.put_nowait(command)

            except xmlrpclib.Fault, fault:
                msg = _("Your request has failed. The reason is:\n%(error)s")
                self.log.error(str(fault))
                self.report_error(jid, msg, {'error': fault.faultString})
            except xmlrpclib.Error, err:
                msg = _("A serious error occured while processing your request:\n%(error)s")
                self.log.error(str(err))
                self.report_error(jid, msg, {'error': str(err)})
            except Exception, exc:
                msg = _("An internal error has occured, please contact the administrator.")
                self.log.critical(str(exc))
                self.report_error(jid, msg)

        finally:
            del self.token
            del self.multicall

    return wrapped_func

class XMLRPCClient(Thread):
    """XMLRPC Client

    It's responsible for performing XMLRPC operations on
    a wiki, as inctructed by command objects received from
    the XMPP component"""

    def __init__(self, config, commands_in, commands_out):
        """A constructor

        @param commands_out: an output command queue (to xmpp)
        @param commands_in: an input command queue (from xmpp)

        """
        Thread.__init__(self)
        self.log = logging.getLogger(__name__)

        if not config.secret:
            error = "You must set a (long) secret string!"
            self.log.critical(error)
            raise ConfigurationError(error)

        self.commands_in = commands_in
        self.commands_out = commands_out
        self.config = config
        self.url = config.wiki_url + "?action=xmlrpc2"
        self.connection = self.create_connection()
        self.token = None
        self.multicall = None
        self.stopping = False

        self._cmd_handlers = {cmd.GetPage: self.get_page,
                              cmd.GetPageHTML: self.get_page_html,
                              cmd.GetPageList: self.get_page_list,
                              cmd.GetPageInfo: self.get_page_info,
                              cmd.GetUserLanguage: self.get_language_by_jid,
                              cmd.Search: self.do_search,
                              cmd.RevertPage: self.do_revert}

    def run(self):
        """Starts the server / thread"""
        while True:
            if self.stopping:
                break

            try:
                command = self.commands_in.get(True, 2)
                self.execute_command(command)
            except Queue.Empty:
                pass

    def stop(self):
        """Stop the thread"""
        self.stopping = True

    def create_connection(self):
        return xmlrpclib.ServerProxy(self.url, allow_none=True, verbose=self.config.verbose)

    def execute_command(self, command):
        """Execute commands coming from the XMPP component"""

        cmd_name = command.__class__

        try:
            handler = self._cmd_handlers[cmd_name]
        except KeyError:
            self.log.debug("No such command: " + cmd_name.__name__)
            return

        handler(command)

    def report_error(self, jid, text, data={}):
        """Reports an internal error

        @param jid: Jabber ID that should be informed about the error condition
        @param text: description of the error
        @param data: dictionary used to substitute strings in translated message
        @type data: dict

        """
        # Dummy function, so that the string appears in a .po file
        _ = lambda x: x

        cmddata = {'text': text, 'data': data}
        report = cmd.NotificationCommandI18n(jid, cmddata, msg_type=u"chat", async=False)
        self.commands_out.put_nowait(report)

    def get_auth_token(self, jid):
        """Get an auth token using user's Jabber ID

        @type jid: unicode
        """
        # We have to use a bare JID
        jid = jid.split('/')[0]
        token = self.connection.getJabberAuthToken(jid, self.config.secret)
        if token:
            self.token = token

    def warn_no_credentials(self, jid):
        """Warn a given JID that credentials check failed

        @param jid: full JID to notify about failure
        @type jid: str

        """
        # Dummy function, so that the string appears in a .po file
        _ = lambda x: x

        cmddata = {'text': _("Credentials check failed, you might be unable to see all information.")}
        warning = cmd.NotificationCommandI18n([jid], cmddata, async=False)
        self.commands_out.put_nowait(warning)

    def _get_multicall_result(self, jid):
        """Returns multicall results and issues a warning if there's an auth error

        @param jid: a full JID to use if there's an error
        @type jid: str

        """

        if not self.token:
            result = self.multicall()[0]
            token_result = u"FAILURE"
        else:
            token_result, result = self.multicall()

        if token_result != u"SUCCESS":
            self.warn_no_credentials(jid)

        return result


    def get_page(self, command):
        """Returns a raw page"""

        self.multicall.getPage(command.pagename)
        command.data = self._get_multicall_result(command.jid)

    get_page = _xmlrpc_decorator(get_page)


    def get_page_html(self, command):
        """Returns a html-formatted page"""

        self.multicall.getPageHTML(command.pagename)
        command.data = self._get_multicall_result(command.jid)

    get_page_html = _xmlrpc_decorator(get_page_html)


    def get_page_list(self, command):
        """Returns a list of all accesible pages"""

        # Dummy function, so that the string appears in a .po file
        _ = lambda x: x

        cmd_data = {'text': _("This command may take a while to complete, please be patient...")}
        info = cmd.NotificationCommandI18n([command.jid], cmd_data, async=False, msg_type=u"chat")
        self.commands_out.put_nowait(info)

        self.multicall.getAllPages()
        command.data = self._get_multicall_result(command.jid)

    get_page_list = _xmlrpc_decorator(get_page_list)


    def get_page_info(self, command):
        """Returns detailed information about a given page"""

        self.multicall.getPageInfo(command.pagename)
        command.data = self._get_multicall_result(command.jid)

    get_page_info = _xmlrpc_decorator(get_page_info)

    def do_search(self, command):
        """Performs a search"""

        # Dummy function, so that the string appears in a .po file
        _ = lambda x: x

        cmd_data = {'text': _("This command may take a while to complete, please be patient...")}
        info = cmd.NotificationCommandI18n([command.jid], cmd_data, async=False, msg_type=u"chat")
        self.commands_out.put_nowait(info)

        c = command
        self.multicall.searchPagesEx(c.term, c.search_type, 30, c.case, c.mtime, c.regexp)
        command.data = self._get_multicall_result(command.jid)

    do_search = _xmlrpc_decorator(do_search)

    def do_revert(self, command):
        """Performs a page revert"""

        # Dummy function, so that the string appears in a .po file
        _ = lambda x: x

        self.multicall.revertPage(command.pagename, command.revision)
        data = self._get_multicall_result(command.jid)

        if type(data) == bool and data:
            cmd_data = {'text': _("Page has been reverted.")}
        elif isinstance(str, data) or isinstance(unicode, data):
            cmd_data = {'text': _("Revert failed: %(reason)s" % {'reason': data})}
        else:
            cmd_data = {'text': _("Revert failed.")}

        info = cmd.NotificationCommandI18n([command.jid], cmd_data, async=False, msg_type=u"chat")
        self.commands_out.put_nowait(info)

    do_revert = _xmlrpc_decorator(do_revert)

    def get_language_by_jid(self, command):
        """Returns language of the a user identified by the given JID"""

        server = xmlrpclib.ServerProxy(self.config.wiki_url + "?action=xmlrpc2")
        language = "en"

        try:
            language = server.getUserLanguageByJID(command.jid)
        except xmlrpclib.Fault, fault:
            self.log.error(str(fault))
        except xmlrpclib.Error, err:
            self.log.error(str(err))
        except Exception, exc:
            self.log.critical(str(exc))

        command.language = language
        self.commands_out.put_nowait(command)


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
        self.log = logging.getLogger(__name__)
        self.config = config

        if config.secret:
            self.secret = config.secret
        else:
            error = "You must set a (long) secret string"
            self.log.critical(error)
            raise ConfigurationError(error)

        self.server = None

    def run(self):
        """Starts the server / thread"""

        self.server = SimpleXMLRPCServer((self.config.xmlrpc_host, self.config.xmlrpc_port))

        # Register methods having an "export" attribute as XML RPC functions and
        # decorate them with a check for a shared (wiki-bot) secret.
        items = self.__class__.__dict__.items()
        methods = [(name, func) for (name, func) in items if callable(func)
                   and "export" in func.__dict__]

        for name, func in methods:
            self.server.register_function(self.secret_check(func), name)

        self.server.serve_forever()

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


    def send_notification(self, jids, notification):
        """Instructs the XMPP component to send a notification

        The notification dict has following entries:
        'text' - notification text (REQUIRED)
        'subject' - notification subject
        'url_list' - a list of dicts describing attached URLs

        @param jids: a list of JIDs to send a message to (bare JIDs)
        @type jids: a list of str or unicode
        @param notification: dictionary with notification data
        @type notification: dict

        """
        command = cmd.NotificationCommand(jids, notification, async=True)
        self.commands.put_nowait(command)
        return True
    send_notification.export = True

    def addJIDToRoster(self, jid):
        """Instructs the XMPP component to add a new JID to its roster

        @param jid: a jid to add, this must be a bare jid
        @type jid: str or unicode,

        """
        command = cmd.AddJIDToRosterCommand(jid)
        self.commands.put_nowait(command)
        return True
    addJIDToRoster.export = True

    def removeJIDFromRoster(self, jid):
        """Instructs the XMPP component to remove a JID from its roster

        @param jid: a jid to remove, this must be a bare jid
        @type jid: str or unicode

        """
        command = cmd.RemoveJIDFromRosterCommand(jid)
        self.commands.put_nowait(command)
        return True
    removeJIDFromRoster.export = True
