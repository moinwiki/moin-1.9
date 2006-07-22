# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SyncPages action

    This action allows you to synchronise pages of two wikis.

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import os
import zipfile
import xmlrpclib
from datetime import datetime

from MoinMoin import wikiutil, config, user
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page
from MoinMoin.wikidicts import Dict

class ActionStatus(Exception): pass

class RemoteWiki(object):
    """ This class should be the base for all implementations of remote wiki
        classes. """
    def getInterwikiName(self):
        """ Returns the interwiki name of the other wiki. """
        return NotImplemented
    
    def __repr__(self):
        """ Returns a representation of the instance for debugging purposes. """
        return NotImplemented

class MoinWiki(RemoteWiki):
    def __init__(self, interwikiname):
        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, '%s:""' % (interwikiname, ))
        self.wiki_url = wikiutil.mapURL(self.request, wikiurl)
        self.valid = not wikitag_bad
        self.xmlrpc_url = self.wiki_url + "?action=xmlrpc2"
        self.connection = self.createConnection()

    def createConnection(self):
        return xmlrpclib.ServerProxy(self.xmlrpc_url, allow_none=True)

    # Methods implementing the RemoteWiki interface
    def getInterwikiName(self):
        return self.connection.interwikiName()

    def __repr__(self):
        return "<RemoteWiki wiki_url=%r valid=%r>" % (self.valid, self.wiki_url)

class ActionClass:
    def __init__(self, pagename, request):
        self.request = request
        self.pagename = pagename
        self.page = Page(request, pagename)

    def parsePage(self):
        defaults = {
            "remotePrefix": "",
            "localPrefix": "",
            "remoteWiki": ""
        }
        
        defaults.update(Dict(self.request, self.pagename).get_dict())
        return defaults
        
    def render(self):
        """ Render action

        This action returns a wiki page with optional message, or
        redirects to new page.
        """
        _ = self.request.getText
        
        params = self.parsePage()
        
        try:
            if not self.request.cfg.interwikiname:
                raise ActionStatus(_("Please set an interwikiname in your wikiconfig (see HelpOnConfiguration) to be able to use this action."))

            if not params["remoteWiki"]:
                raise ActionStatus(_("Incorrect parameters. Please supply at least the ''remoteWiki'' parameter."))
            
            remote = MoinWiki(params["remoteWiki"])
            
            if not remote.valid:
                raise ActionStatus(_("The ''remoteWiki'' is unknown."))
            
            # ...
            self.sync(params)
        except ActionStatus, e:
            return self.page.send_page(self.request, msg=u'<p class="error">%s</p>\n' % (e.args[0], ))

        return self.page.send_page(self.request, msg=_("Syncronisation finished."))
    
def execute(pagename, request):
    ActionClass(pagename, request).render()
