# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a xmlrpc server and client for the notification bot

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import datetime, logging, time, xmlrpclib, Queue
from SimpleXMLRPCServer import SimpleXMLRPCServer
from threading import Thread

import jabberbot.commands as cmd
from jabberbot.multicall import MultiCall
from jabberbot.i18n import getText

_ = getText

class ConfigurationError(Exception):
    def __init__(self, message):
        self.message = message

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
        self.log = logging.getLogger("log")

        if not config.secret:
            error = _("You must set a (long) secret string!")
            self.log.critical(error)
            raise ConfigurationError(error)

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
        elif isinstance(command, cmd.GetPageInfo):
            self.get_page_info(command)
        elif isinstance(command, cmd.GetUserLanguage):
            self.get_language_by_jid(command)

    def report_error(self, jid, text):
        report = cmd.NotificationCommand(jid, text, _("Error"), async=False)
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

    def _xmlrpc_decorator(function):
        """A decorator function, which adds some maintenance code

        This function takes care of preparing a MultiCall object and
        an authentication token, and deleting them at the end.

        """
        def wrapped_func(self, command):
            self.token = None
            self.multicall = MultiCall(self.connection)
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
                    msg = _("Your request has failed. The reason is:\n%s")
                    self.log.error(str(fault))
                    self.report_error(jid, msg % (fault.faultString, ))
                except xmlrpclib.Error, err:
                    msg = _("A serious error occured while processing your request:\n%s")
                    self.log.error(str(err))
                    self.report_error(jid, msg % (str(err), ))
                except Exception, exc:
                    msg = _("An internal error has occured, please contact the administrator.")
                    self.log.critical(str(exc))
                    self.report_error(jid, msg)

            finally:
                del self.token
                del self.multicall

        return wrapped_func

    def warn_no_credentials(self, jid):
        msg = _("Credentials check failed, you may be unable to see all information.")
        warning = cmd.NotificationCommand([jid], msg, async=False)
        self.commands_out.put_nowait(warning)

    def get_page(self, command):
        """Returns a raw page"""

        self.multicall.getPage(command.pagename)

        if not self.token:
            self.warn_no_credentials(command.jid)
            getpage_result = self.multicall()[0]
        else:
            token_result, getpage_result = self.multicall()
            if token_result != u"SUCCESS":
                self.warn_no_credentials(command.jid)

        command.data = getpage_result

    get_page = _xmlrpc_decorator(get_page)


    def get_page_html(self, command):
        """Returns a html-formatted page"""

        self.multicall.getPageHTML(command.pagename)

        if not self.token:
            self.warn_no_credentials(command.jid)
            getpagehtml_result = self.multicall()[0]
        else:
            token_result, getpagehtml_result = self.multicall()
            if token_result != u"SUCCESS":
                self.warn_no_credentials(command.jid)

        command.data = getpagehtml_result

    get_page_html = _xmlrpc_decorator(get_page_html)


    def get_page_list(self, command):
        """Returns a list of all accesible pages"""

        txt = _("This command may take a while to complete, please be patient...")
        info = cmd.NotificationCommand([command.jid], txt, async=False)
        self.commands_out.put_nowait(info)

        self.multicall.getAllPages()

        if not self.token:
            # FIXME: notify the user that he may not have full rights on the wiki
            getpagelist_result = self.multicall()[0]
        else:
            token_result, getpagelist_result = self.multicall()
            if token_result != u"SUCCESS":
                self.warn_no_credentials(command.jid)

        command.data = getpagelist_result

    get_page_list = _xmlrpc_decorator(get_page_list)


    def get_page_info(self, command):
        """Returns detailed information about a given page"""

        self.multicall.getPageInfo(command.pagename)

        if not self.token:
            self.warn_no_credentials(command.jid)
            getpageinfo_result = self.multicall()[0]
        else:
            token_result, getpageinfo_result = self.multicall()
            if token_result != u"SUCCESS":
                self.warn_no_credentials(jid)

        author = getpageinfo_result['author']
        if author.startswith("Self:"):
            author = getpageinfo_result['author'][5:]

        datestr = str(getpageinfo_result['lastModified'])
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
             'version': getpageinfo_result['version'],
         }

        command.data = msg

    get_page_info = _xmlrpc_decorator(get_page_info)

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
        self.log = logging.getLogger("log")

        if config.secret:
            self.secret = config.secret
        else:
            error = _("You must set a (long) secret string")
            self.log.critical(error)
            raise ConfigurationError(error)

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

    def secret_check(self, function):
        """Adds a check for a secret to a given function

        Using this one does not have to worry about checking for the secret
        in every XML RPC function.
        """
        def protected_func(secret, *args):
            if secret != self.secret:
                raise xmlrpclib.Fault(1, _("You are not allowed to use this bot!"))
            else:
                return function(self, *args)

        return protected_func


    def send_notification(self, jids, text, subject):
        """Instructs the XMPP component to send a notification

        @param jids: a list of JIDs to send a message to (bare JIDs)
        @type jids: a list of str or unicode
        @param text: a message body
        @type text: unicode

        """
        command = cmd.NotificationCommand(jids, text, subject)
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
