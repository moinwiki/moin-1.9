# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - a xmlrpc server and client for the notification bot

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import Queue
import datetime, logging, time, xmlrpclib
from threading import Thread
from SimpleXMLRPCServer import SimpleXMLRPCServer

import jabberbot.commands as cmd
from jabberbot.multicall import MultiCall

class ConfigurationError(Exception):
    def __init__(self, message):
        self.message = message

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
        self.log = logging.getLogger("log")

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

    def get_auth_token(self, jid):
        token = self.connection.getAuthToken(jid, self.config.secret)
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

            try:
                try:
                    self.get_auth_token(command.jid)
                    if self.token:
                        self.multicall.applyAuthToken(self.token)

                    function(self, command)
                    self.commands_out.put_nowait(command)
                except xmlrpclib.Fault, fault:
                    msg = u"""Your request has failed. The reason is:\n%s"""
                    notification = cmd.NotificationCommand([jid], msg % (fault.faultString, ))
                    self.commands_out.put_nowait(notification)
                except xmlrpclib.Error, err:
                    msg = u"""A serious error occured while processing your request:\n%s"""
                    notification = cmd.NotificationCommand([jid], msg % (str(err), ))
                    self.commands_out.put_nowait(notification)

            finally:
                del self.token
                del self.multicall

        return wrapped_func

    def warn_no_credentials(self, jid):
        msg = u"""Credentials check failed, you may be unable to see all information."""
        warning = cmd.NotificationCommand([jid], msg)
        self.commands_out.put_nowait(warning)

    def get_page(self, command):
        """Returns a raw page"""

        self.multicall.getPage(command.pagename)

        if not self.token:
            self.warn_no_credentials(command.jid)
            getpage_result = self.multicall()
        else:
            getpage_result, token_result = self.multicall()

        # FIXME: warn if token turned out being wrong
        command.data = getpage_result[0]

    get_page = _xmlrpc_decorator(get_page)


    def get_page_html(self, command):
        """Returns a html-formatted page"""

        self.multicall.getPageHTML(command.pagename)

        if not self.token:
            self.warn_no_credentials(command.jid)
            getpagehtml_result = self.multicall()
        else:
            token_result, getpagehtml_result = self.multicall()

        # FIXME: warn if token turned out being wrong
        command.data = getpagehtml_result[0]

    get_page_html = _xmlrpc_decorator(get_page_html)


    def get_page_list(self, command):
        """Returns a list of all accesible pages"""

        txt = u"""This command may take a while to complete, please be patient..."""
        info = cmd.NotificationCommand([command.jid], txt)
        self.commands_out.put_nowait(info)

        self.multicall.getAllPages()

        if not self.token:
            # FIXME: notify the user that he may not have full rights on the wiki
            getpagelist_result = self.multicall()
        else:
            token_result, getpagelist_result = self.multicall()

        # FIXME: warn if token turned out being wrong
        command.data = getpagelist_result[0]

    get_page_list = _xmlrpc_decorator(get_page_list)


    def get_page_info(self, command):
        """Returns detailed information about a given page"""

        self.multicall.getPageInfo(command.pagename)

        if not self.token:
            # FIXME: notify the user that he may not have full rights on the wiki
            getpageinfo_result = self.multicall()
        else:
            token_result, getpageinfo_result = self.multicall()

        # FIXME: warn if token turned out being wrong

        author = getpageinfo_result[0]['author']
        if author.startswith("Self:"):
            author = getpageinfo_result[0]['author'][5:]

        datestr = str(getpageinfo_result[0]['lastModified'])
        date = u"%(year)s-%(month)s-%(day)s at %(time)s" % {
                    'year': datestr[:4],
                    'month': datestr[4:6],
                    'day': datestr[6:8],
                    'time': datestr[9:17],
                }

        msg = u"""Last author: %(author)s
Last modification: %(modification)s
Current version: %(version)s""" % {
             'author': author,
             'modification': date,
             'version': getpageinfo_result[0]['version'],
         }

        command.data = msg

    get_page_info = _xmlrpc_decorator(get_page_info)


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
            error = "You must set a (long) secret string"
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
                raise xmlrpclib.Fault(1, "You are not allowed to use this bot!")
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
