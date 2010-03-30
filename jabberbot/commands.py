# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - inter-thread communication commands

    This file defines command objects used by notification
    bot's threads to communicate among each other.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from pyxmpp.jid import JID

# First, XML RPC -> XMPP commands
class NotificationCommand:
    """Class representing a notification request"""
    def __init__(self, jids, notification, msg_type=u"normal", async=True):
        """A constructor

        @param jids: a list of jids to sent this message to
        @param notification: dictionary with notification data
        @param async: async notifications get queued if contact is DnD
        @type jids: list

        """
        if type(jids) != list:
            raise Exception("jids argument must be a list!")

        self.notification = notification
        self.jids = jids
        self.async = async
        self.msg_type = msg_type

class NotificationCommandI18n(NotificationCommand):
    """Notification request that should be translated by the XMPP bot"""
    def __init__(self, jids, notification, msg_type="normal", async=True):
        """A constructor

        Params as in NotificationCommand.

        """
        NotificationCommand.__init__(self, jids, notification, msg_type, async)

    def translate(self, gettext_func):
        """Translate the message using a provided gettext function

        @param gettext_func: a unary gettext function
        @return: translated message and subject
        @rtype: tuple
        """
        if self.notification.has_key('data'):
            msg =  gettext_func(self.notification['text']) % self.notification['data']
        else:
            msg = gettext_func(self.notification['text'])

        return (msg, gettext_func(self.notification.get('subject', '')))

class AddJIDToRosterCommand:
    """Class representing a request to add a new jid to roster"""
    def __init__(self, jid):
        self.jid = jid

class RemoveJIDFromRosterCommand:
    """Class representing a request to remove a jid from roster"""
    def __init__(self, jid):
        self.jid = jid

# XMPP <-> XML RPC commands
# These commands are passed in both directions, with added data
# payload when they return to the XMPP code. Naming convention
# follows method names defined by the Wiki RPC Interface v2.

class BaseDataCommand(object):
    """Base class for all commands used by the XMPP component.

    It has to support an optional data payload and store JID the
    request has come from and provide a help string for its parameters.
    """

    # Description of what the command does
    description = u""

    # Parameter list in a human-readable format
    parameter_list = u""

    def __init__(self, jid, presentation=u"text"):
        """A constructor

        @param jid: Jabber ID to send the reply to
        @param presentation: how to display results; "text" or "dataforms"
        @type jid: unicode
        @type presentation: unicode

        """
        self.jid = jid
        self.data = None
        self.presentation = presentation

class GetPage(BaseDataCommand):

    description = u"retrieve raw content of a named page"
    parameter_list = u"pagename"

    def __init__(self, jid, pagename):
        BaseDataCommand.__init__(self, jid)
        self.pagename = pagename

class GetPageHTML(BaseDataCommand):

    description = u"retrieve HTML-formatted content of a named page"
    parameter_list = u"pagename"

    def __init__(self, jid, pagename):
        BaseDataCommand.__init__(self, jid)
        self.pagename = pagename

class GetPageList(BaseDataCommand):

    description = u"get a list of accesible pages"
    parameter_list = u""

    def __init__(self, jid):
        BaseDataCommand.__init__(self, jid)

class GetPageInfo(BaseDataCommand):

    description = u"show detailed information about a page"
    parameter_list = u"pagename"

    def __init__(self, jid, pagename, presentation=u"text"):
        BaseDataCommand.__init__(self, jid, presentation)
        self.pagename = pagename

class Search(BaseDataCommand):

    description = u"perform a wiki search"
    parameter_list = u"{title|text} term"

    def __init__(self, jid, search_type, *args, **kwargs):
        BaseDataCommand.__init__(self, jid)

        if not JID(jid).resource:
            raise ValueError("The jid argument must be a full jabber id!")

        self.term = ' '.join(args)
        self.search_type = search_type
        self.presentation = kwargs.get('presentation', 'text') # "text" or "dataforms"
        self.case = kwargs.get('case', False)
        self.mtime = None
        self.regexp = kwargs.get('regexp', False)


class RevertPage(BaseDataCommand):

    description = u"revert a page to previous revision"
    parameter_list = u"page_name revision"

    def __init__(self, jid, pagename, revision):
        BaseDataCommand.__init__(self, jid)
        self.pagename = pagename
        self.revision = revision


class GetUserLanguage:
    """Request user's language information from wiki"""

    def __init__(self, jid):
        """
        @param jid: user's (bare) Jabber ID
        """
        self.jid = jid
        self.language = None

