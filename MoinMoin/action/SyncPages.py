# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SyncPages action

    This action allows you to synchronise pages of two wikis.

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import os
import re
import zipfile
import xmlrpclib
from datetime import datetime

from MoinMoin import wikiutil, config, user
from MoinMoin.packages import unpackLine
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page
from MoinMoin.wikidicts import Dict

class ActionStatus(Exception): pass

class RemotePage(object):
    """ This class represents a page in (another) wiki. """
    def __init__(self, name, revno):
        self.name = name
        self.revno = revno

class RemoteWiki(object):
    """ This class should be the base for all implementations of remote wiki
        classes. """

    def __repr__(self):
        """ Returns a representation of the instance for debugging purposes. """
        return NotImplemented

    def getInterwikiName(self):
        """ Returns the interwiki name of the other wiki. """
        return NotImplemented

    def getRemotePages(self):
        """ Returns a list of RemotePage instances. """
        return NotImplemented

class MoinWiki(RemoteWiki):
    def __init__(self, interwikiname):
        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, '%s:""' % (interwikiname, ))
        self.wiki_url = wikiutil.mapURL(self.request, wikiurl)
        self.valid = not wikitag_bad
        self.xmlrpc_url = self.wiki_url + "?action=xmlrpc2"
        self.connection = self.createConnection()
        # XXX add version and interwiki name checking!

    def createConnection(self):
        return xmlrpclib.ServerProxy(self.xmlrpc_url, allow_none=True)

    # Methods implementing the RemoteWiki interface
    def getInterwikiName(self):
        return self.connection.interwikiName()

    def getRemotePages(self):
        pages = self.connection.getAllPagesEx({"include_revno": True})
        return [RemotePage(unicode(name), revno) for name, revno in pages]

    def __repr__(self):
        return "<RemoteWiki wiki_url=%r valid=%r>" % (self.valid, self.wiki_url)

class ActionClass:
    def __init__(self, pagename, request):
        self.request = request
        self.pagename = pagename
        self.page = Page(request, pagename)

    def parse_page(self):
        options = {
            "remotePrefix": "",
            "localPrefix": "",
            "remoteWiki": "",
            "localMatch": None,
            "remoteMatch": None,
            "pageList": None,
            "groupList": None,
        }

        options.update(Dict(self.request, self.pagename).get_dict())

        # Convert page and group list strings to lists
        if options["pageList"] is not None:
            options["pageList"] = unpackLine(options["pageList"], ",")
        if options["groupList"] is not None:
            options["groupList"] = unpackLine(options["groupList"], ",")

        return options

    def fix_params(self, params):
        """ Does some fixup on the parameters. """

        # merge the pageList case into the remoteMatch case
        if params["pageList"] is not None:
            params["remoteMatch"] = u'|'.join([r'^%s$' % re.escape(name) for name in params["pageList"]])

        if params["localMatch"] is not None:
            params["localMatch"] = re.compile(params["localMatch"], re.U)
        
        if params["remoteMatch"] is not None:
            params["remoteMatch"] = re.compile(params["remoteMatch"], re.U)

        return params

    def render(self):
        """ Render action

        This action returns a status message.
        """
        _ = self.request.getText

        params = self.fix_params(self.parse_page())


        try:
            if not self.request.cfg.interwikiname:
                raise ActionStatus(_("Please set an interwikiname in your wikiconfig (see HelpOnConfiguration) to be able to use this action."))

            if not params["remoteWiki"]:
                raise ActionStatus(_("Incorrect parameters. Please supply at least the ''remoteWiki'' parameter."))

            remote = MoinWiki(params["remoteWiki"])

            if not remote.valid:
                raise ActionStatus(_("The ''remoteWiki'' is unknown."))

            self.sync(params, remote)
        except ActionStatus, e:
            return self.page.send_page(self.request, msg=u'<p class="error">%s</p>\n' % (e.args[0], ))

        return self.page.send_page(self.request, msg=_("Syncronisation finished."))
    
    def sync(self, params, remote):
        """ This method does the syncronisation work. """
        
        r_pages = remote.getRemotePages()

def execute(pagename, request):
    ActionClass(pagename, request).render()
