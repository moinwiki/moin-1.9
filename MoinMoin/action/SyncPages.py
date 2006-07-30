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

# Compatiblity to Python 2.3
try:
    set
except NameError:
    from sets import Set as set


from MoinMoin import wikiutil, config, user
from MoinMoin.packages import unpackLine, packLine
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page
from MoinMoin.wikidicts import Dict, Group


class ActionStatus(Exception): pass

class UnsupportedWikiException(Exception): pass

# Move these classes to MoinMoin.wikisync
class RemotePage(object):
    """ This class represents a page in (another) wiki. """
    def __init__(self, name, revno):
        self.name = name
        self.revno = revno

    def __repr__(self):
        return repr("<Remote Page %r>" % unicode(self))

    def __unicode__(self):
        return u"%s<%i>" % (self.name, self.revno)

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        if not isinstance(other, RemotePage):
            return false
        return self.name == other.name

    def filter(cls, rp_list, regex):
        return [x for x in rp_list if regex.match(x.name)]
    filter = classmethod(filter)


class RemoteWiki(object):
    """ This class should be the base for all implementations of remote wiki
        classes. """

    def __repr__(self):
        """ Returns a representation of the instance for debugging purposes. """
        return NotImplemented

    def getInterwikiName(self):
        """ Returns the interwiki name of the other wiki. """
        return NotImplemented

    def getPages(self):
        """ Returns a list of RemotePage instances. """
        return NotImplemented


class MoinRemoteWiki(RemoteWiki):
    """ Used for MoinMoin wikis reachable via XMLRPC. """
    def __init__(self, request, interwikiname):
        self.request = request
        _ = self.request.getText
        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, '%s:""' % (interwikiname, ))
        self.wiki_url = wikiutil.mapURL(self.request, wikiurl)
        self.valid = not wikitag_bad
        self.xmlrpc_url = self.wiki_url + "?action=xmlrpc2"
        if not self.valid:
            self.connection = None
            return
        self.connection = self.createConnection()
        version = self.connection.getMoinVersion()
        if not isinstance(version, (tuple, list)):
            raise UnsupportedWikiException(_("The remote version of MoinMoin is too old, the version 1.6 is required at least."))
        remote_interwikiname = self.getInterwikiName()
        remote_iwid = self.connection.interwikiName()[1]
        self.is_anonymous = remote_interwikiname is None
        if not self.is_anonymous and interwikiname != remote_interwikiname:
            raise UnsupportedWikiException(_("The remote wiki uses a different InterWiki name (%(remotename)s)"
                                             " internally than you specified (%(localname)s).") % {
                "remotename": remote_interwikiname, "localname": interwikiname})

        if self.is_anonymous:
            self.iwid_full = packLine([remote_iwid])
        else:
            self.iwid_full = packLine([remote_iwid, interwikiname])

    def createConnection(self):
        return xmlrpclib.ServerProxy(self.xmlrpc_url, allow_none=True, verbose=True)

    # Methods implementing the RemoteWiki interface
    def getInterwikiName(self):
        return self.connection.interwikiName()[0]

    def getPages(self):
        pages = self.connection.getAllPagesEx({"include_revno": True, "include_deleted": True})
        return [RemotePage(unicode(name), revno) for name, revno in pages]

    def __repr__(self):
        return "<MoinRemoteWiki wiki_url=%r valid=%r>" % (self.wiki_url, self.valid)


class MoinLocalWiki(RemoteWiki):
    """ Used for the current MoinMoin wiki. """
    def __init__(self, request):
        self.request = request

    def getGroupItems(self, group_list):
        pages = []
        for group_pagename in group_list:
            pages.extend(Group(self.request, group_pagename).members())
        return [self.createRemotePage(x) for x in pages]

    def createRemotePage(self, page_name):
        return RemotePage(page_name, Page(self.request, page_name).get_real_rev())

    # Methods implementing the RemoteWiki interface
    def getInterwikiName(self):
        return self.request.cfg.interwikiname

    def getPages(self):
        return [self.createRemotePage(x) for x in self.request.rootpage.getPageList(exists=0)]

    def __repr__(self):
        return "<MoinLocalWiki>"


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
            params["localMatch"] = params["remoteMatch"] = u'|'.join([r'^%s$' % re.escape(name)
                                                                      for name in params["pageList"]])

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

            local = MoinLocalWiki(self.request)
            try:
                remote = MoinRemoteWiki(self.request, params["remoteWiki"])
            except UnsupportedWikiException, (msg, ):
                raise ActionStatus(msg)

            if not remote.valid:
                raise ActionStatus(_("The ''remoteWiki'' is unknown."))

            self.sync(params, local, remote)
        except ActionStatus, e:
            return self.page.send_page(self.request, msg=u'<p class="error">%s</p>\n' % (e.args[0], ))

        return self.page.send_page(self.request, msg=_("Syncronisation finished."))
    
    def sync(self, params, local, remote):
        """ This method does the syncronisation work. """
        
        r_pages = remote.getPages()
        l_pages = local.getPages()
        print "Got %i local, %i remote pages" % (len(l_pages), len(r_pages))
        if params["localMatch"]:
            l_pages = RemotePage.filter(l_pages, params["localMatch"])
        if params["remoteMatch"]:
            print "Filtering remote pages using regex %r" % params["remoteMatch"].pattern
            r_pages = RemotePage.filter(r_pages, params["remoteMatch"])
        print "After filtering: Got %i local, %i remote pages" % (len(l_pages), len(r_pages))

        if params["groupList"]:
            pages_from_groupList = local.getGroupItems(params["groupList"])
            if not params["localMatch"]:
                l_pages = pages_from_groupList
            else:
                l_pages += pages_from_groupList

        l_pages = set(l_pages)
        r_pages = set(r_pages)
        
        # XXX this is not correct if matching is active
        remote_but_not_local = r_pages - l_pages
        local_but_not_remote = l_pages - r_pages
        
        # some initial test code
        r_new_pages = u", ".join([unicode(x) for x in remote_but_not_local])
        l_new_pages = u", ".join([unicode(x) for x in local_but_not_remote])
        raise ActionStatus("These pages are in the remote wiki, but not local: " + r_new_pages + "<br>These pages are in the local wiki, but not in the remote one: " + l_new_pages)


def execute(pagename, request):
    ActionClass(pagename, request).render()
