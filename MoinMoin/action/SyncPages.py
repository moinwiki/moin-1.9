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
from MoinMoin.PageEditor import PageEditor, conflict_markers
from MoinMoin.Page import Page
from MoinMoin.wikidicts import Dict, Group
from MoinMoin.wikisync import TagStore
from MoinMoin.util.bdiff import decompress, patch, compress, textdiff
from MoinMoin.util import diff3

# directions
UP, DOWN, BOTH = range(3)
directions_map = {"up": UP, "down": DOWN, "both": BOTH}


def normalise_pagename(page_name, prefix):
    """ Checks if the page_name starts with the prefix.
        Returns None if it does not, otherwise strips the prefix.
    """
    if prefix:
        if not page_name.startswith(prefix):
            return None
        else:
            return page_name[len(prefix):]
    else:
        return page_name


class ActionStatus(Exception): pass

class UnsupportedWikiException(Exception): pass

# XXX Move these classes to MoinMoin.wikisync
class SyncPage(object):
    """ This class represents a page in one or two wiki(s). """
    def __init__(self, name, local_rev=None, remote_rev=None, local_name=None, remote_name=None):
        """ Creates a SyncPage instance.
            @param name: The canonical name of the page, without prefixes.
            @param local_rev: The revision of the page in the local wiki.
            @param remote_rev: The revision of the page in the remote wiki.
            @param local_name: The page name of the page in the local wiki.
            @param remote_name: The page name of the page in the remote wiki.
        """
        self.name = name
        self.local_rev = local_rev
        self.remote_rev = remote_rev
        self.local_name = local_name
        self.remote_name = remote_name
        assert local_rev or remote_rev
        assert local_name or remote_name

    def __repr__(self):
        return repr("<Remote Page %r>" % unicode(self))

    def __unicode__(self):
        return u"%s[%s|%s]<%r:%r>" % (self.name, self.local_name, self.remote_name, self.local_rev, self.remote_rev)

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        """ Ensures that the hash value of this page only depends on the canonical name. """
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, SyncPage):
            return false
        return self.name == other.name

    def add_missing_pagename(self, local, remote):
        """ Checks if the particular concrete page names are unknown and fills
            them in.
        """
        if self.local_name is None:
            n_name = normalise_pagename(self.remote_name, remote.prefix)
            assert n_name is not None
            self.local_name = (local.prefix or "") + n_name
        elif self.remote_name is None:
            n_name = normalise_pagename(self.local_name, local.prefix)
            assert n_name is not None
            self.remote_name = (local.prefix or "") + n_name

        return self # makes using list comps easier

    def filter(cls, sp_list, func):
        """ Returns all pages in sp_list that let func return True
            for the canonical page name.
        """
        return [x for x in sp_list if func(x.name)]
    filter = classmethod(filter)

    def merge(cls, local_list, remote_list):
        """ Merges two lists of SyncPages into one, migrating attributes like the names. """
        # map page names to SyncPage objects :-)
        d = dict(zip(local_list, local_list))
        for sp in remote_list:
            if sp in d:
                d[sp].remote_rev = sp.remote_rev
                d[sp].remote_name = sp.remote_name
            else:
                d[sp] = sp
        return d.keys()
    merge = classmethod(merge)

    def is_only_local(self):
        """ Is true if the page is only in the local wiki. """
        return not self.remote_rev

    def is_only_remote(self):
        """ Is true if the page is only in the remote wiki. """
        return not self.local_rev

    def is_local_and_remote(self):
        """ Is true if the page is in both wikis. """
        return self.local_rev and self.remote_rev

    def iter_local_only(cls, sp_list):
        """ Iterates over all pages that are local only. """
        for x in sp_list:
            if x.is_only_local():
                yield x
    iter_local_only = classmethod(iter_local_only)

    def iter_remote_only(cls, sp_list):
        """ Iterates over all pages that are remote only. """
        for x in sp_list:
            if x.is_only_remote():
                yield x
    iter_remote_only = classmethod(iter_remote_only)

    def iter_local_and_remote(cls, sp_list):
        """ Iterates over all pages that are local and remote. """
        for x in sp_list:
            if x.is_local_and_remote():
                yield x
    iter_local_and_remote = classmethod(iter_local_and_remote)

class RemoteWiki(object):
    """ This class should be the base for all implementations of remote wiki
        classes. """

    def __repr__(self):
        """ Returns a representation of the instance for debugging purposes. """
        return NotImplemented

    def get_interwiki_name(self):
        """ Returns the interwiki name of the other wiki. """
        return NotImplemented

    def get_iwid(self):
        """ Returns the InterWiki ID. """
        return NotImplemented

    def get_pages(self, **kwargs):
        """ Returns a list of SyncPage instances. """
        return NotImplemented


class MoinRemoteWiki(RemoteWiki):
    """ Used for MoinMoin wikis reachable via XMLRPC. """
    def __init__(self, request, interwikiname, prefix):
        self.request = request
        self.prefix = prefix
        _ = self.request.getText

        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, '%s:""' % (interwikiname, ))
        self.wiki_url = wikiutil.mapURL(self.request, wikiurl)
        self.valid = not wikitag_bad
        self.xmlrpc_url = self.wiki_url + "?action=xmlrpc2"
        if not self.valid:
            self.connection = None
            return

        self.connection = self.createConnection()

        iw_list = self.connection.interwikiName()

        #version = self.connection.getMoinVersion()
        #if not isinstance(version, (tuple, list)):
        #    raise UnsupportedWikiException(_("The remote version of MoinMoin is too old, the version 1.6 is required at least."))

        self.remote_interwikiname = remote_interwikiname = iw_list[0]
        self.remote_iwid = remote_iwid = iw_list[1]
        self.is_anonymous = remote_interwikiname is None
        if not self.is_anonymous and interwikiname != remote_interwikiname:
            raise UnsupportedWikiException(_("The remote wiki uses a different InterWiki name (%(remotename)s)"
                                             " internally than you specified (%(localname)s).") % {
                "remotename": wikiutil.escape(remote_interwikiname), "localname": wikiutil.escape(interwikiname)})

        if self.is_anonymous:
            self.iwid_full = packLine([remote_iwid])
        else:
            self.iwid_full = packLine([remote_iwid, interwikiname])

    def createConnection(self):
        return xmlrpclib.ServerProxy(self.xmlrpc_url, allow_none=True, verbose=True)

    # Public methods
    def get_diff(self, pagename, from_rev, to_rev):
        """ Returns the binary diff of the remote page named pagename, given
            from_rev and to_rev. """
        result = self.connection.getDiff(pagename, from_rev, to_rev)
        result["diff"] = str(result["diff"]) # unmarshal Binary object
        return result

    def merge_diff(self, pagename, diff, local_rev, delta_remote_rev, last_remote_rev, interwiki_name):
        """ Merges the diff into the page on the remote side. """
        result = self.connection.mergeDiff(pagename, xmlrpclib.Binary(diff), local_rev, delta_remote_rev, last_remote_rev, interwiki_name)
        return result

    # Methods implementing the RemoteWiki interface
    def get_interwiki_name(self):
        return self.remote_interwikiname

    def get_iwid(self):
        return self.remote_iwid

    def get_pages(self, **kwargs):
        options = {"include_revno": True,
                   "include_deleted": True,
                   "exclude_non_writable": kwargs["exclude_non_writable"]}
        pages = self.connection.getAllPagesEx(options)
        rpages = []
        for name, revno in pages:
            normalised_name = normalise_pagename(name, self.prefix)
            if normalised_name is None:
                continue
            rpages.append(SyncPage(normalised_name, remote_rev=revno, remote_name=name))
        return rpages

    def __repr__(self):
        return "<MoinRemoteWiki wiki_url=%r valid=%r>" % (self.wiki_url, self.valid)


class MoinLocalWiki(RemoteWiki):
    """ Used for the current MoinMoin wiki. """
    def __init__(self, request, prefix):
        self.request = request
        self.prefix = prefix

    def getGroupItems(self, group_list):
        """ Returns all page names that are listed on the page group_list. """
        pages = []
        for group_pagename in group_list:
            pages.extend(Group(self.request, group_pagename).members())
        return [self.createSyncPage(x) for x in pages]

    def createSyncPage(self, page_name):
        normalised_name = normalise_pagename(page_name, self.prefix)
        if normalised_name is None:
            return None
        return SyncPage(normalised_name, local_rev=Page(self.request, page_name).get_real_rev(), local_name=page_name)

    # Public methods:

    # Methods implementing the RemoteWiki interface
    def get_interwiki_name(self):
        return self.request.cfg.interwikiname

    def get_iwid(self):
        return self.request.cfg.iwid

    def get_pages(self, **kwargs):
        assert not kwargs
        return [x for x in [self.createSyncPage(x) for x in self.request.rootpage.getPageList(exists=0)] if x]

    def __repr__(self):
        return "<MoinLocalWiki>"


class ActionClass:
    INFO, WARN, ERROR = range(3) # used for logging

    def __init__(self, pagename, request):
        self.request = request
        self.pagename = pagename
        self.page = Page(request, pagename)
        self.status = []

    def log_status(self, level, message):
        """ Appends the message with a given importance level to the internal log. """
        self.status.append((level, message))

    def parse_page(self):
        """ Parses the parameter page and returns the read arguments. """
        options = {
            "remotePrefix": "",
            "localPrefix": "",
            "remoteWiki": "",
            "pageMatch": None,
            "pageList": None,
            "groupList": None,
            "direction": "foo", # is defaulted below
        }

        options.update(Dict(self.request, self.pagename).get_dict())

        # Convert page and group list strings to lists
        if options["pageList"] is not None:
            options["pageList"] = unpackLine(options["pageList"], ",")
        if options["groupList"] is not None:
            options["groupList"] = unpackLine(options["groupList"], ",")

        options["direction"] = directions_map.get(options["direction"], BOTH)

        return options

    def fix_params(self, params):
        """ Does some fixup on the parameters. """

        # merge the pageList case into the pageMatch case
        if params["pageList"] is not None:
            params["pageMatch"] = u'|'.join([r'^%s$' % re.escape(name)
                                             for name in params["pageList"]])
            del params["pageList"]

        if params["pageMatch"] is not None:
            params["pageMatch"] = re.compile(params["pageMatch"], re.U)

        # we do not support matching or listing pages if there is a group of pages
        if params["groupList"]:
            params["pageMatch"] = None

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

            local = MoinLocalWiki(self.request, params["localPrefix"])
            try:
                remote = MoinRemoteWiki(self.request, params["remoteWiki"], params["remotePrefix"])
            except UnsupportedWikiException, (msg, ):
                raise ActionStatus(msg)

            if not remote.valid:
                raise ActionStatus(_("The ''remoteWiki'' is unknown."))

            self.sync(params, local, remote)
        except ActionStatus, e:
            msg = u'<p class="error">%s</p><p>%s</p>\n' % (e.args[0], repr(self.status))
        else:
            msg = u"%s<p>%s</p>" % (_("Syncronisation finished."), repr(self.status))

        # XXX append self.status to the job page
        return self.page.send_page(self.request, msg=msg)
    
    def sync(self, params, local, remote):
        """ This method does the syncronisation work. """
        _ = self.request.getText

        l_pages = local.get_pages()
        r_pages = remote.get_pages(exclude_non_writable=direction != DOWN)

        if params["groupList"]:
            pages_from_groupList = set(local.getGroupItems(params["groupList"]))
            r_pages = SyncPage.filter(r_pages, pages_from_groupList.__contains__)
            l_pages = SyncPage.filter(l_pages, pages_from_groupList.__contains__)

        m_pages = [elem.add_missing_pagename(local, remote) for elem in SyncPage.merge(l_pages, r_pages)]

        print "Got %i local, %i remote pages, %i merged pages" % (len(l_pages), len(r_pages), len(m_pages))
        
        if params["pageMatch"]:
            m_pages = SyncPage.filter(m_pages, params["pageMatch"].match)
        print "After filtering: Got %i merges pages" % (len(m_pages), )

        on_both_sides = list(SyncPage.iter_local_and_remote(m_pages))
        remote_but_not_local = list(SyncPage.iter_remote_only(m_pages))
        local_but_not_remote = list(SyncPage.iter_local_only(m_pages))
        
        # some initial test code (XXX remove)
        #r_new_pages = u", ".join([unicode(x) for x in remote_but_not_local])
        #l_new_pages = u", ".join([unicode(x) for x in local_but_not_remote])
        #raise ActionStatus("These pages are in the remote wiki, but not local: " + wikiutil.escape(r_new_pages) + "<br>These pages are in the local wiki, but not in the remote one: " + wikiutil.escape(l_new_pages))

        # let's do the simple case first, can be refactored later to match all cases
        # XXX handle deleted pages
        for rp in on_both_sides:
            # XXX add locking, acquire read-lock on rp
            print "Processing %r" % rp

            local_pagename = rp.local_name
            current_page = PageEditor(self.request, local_pagename)
            current_rev = current_page.get_real_rev()

            tags = TagStore(current_page)
            matching_tags = tags.fetch(iwid_full=remote.iwid_full)
            matching_tags.sort()
            #print "------ TAGS: " + repr(matching_tags) + repr(tags.tags)

            if not matching_tags:
                remote_rev = None
                local_rev = rp.local_rev # merge against the newest version
                old_contents = ""
            else:
                newest_tag = matching_tags[-1]
                local_rev = newest_tag.current_rev
                remote_rev = newest_tag.remote_rev
                if remote_rev == rp.remote_rev and local_rev == current_rev:
                    continue # no changes done, next page
                old_page = Page(self.request, local_pagename, rev=local_rev)
                old_contents = old_page.get_raw_body_str()

            self.log_status(ActionClass.INFO, _("Synchronising page %(pagename)s with remote page %(remotepagename)s ...") % {"pagename": local_pagename, "remotepagename": rp.remote_name})

            diff_result = remote.get_diff(rp.remote_name, remote_rev, None) # XXX might raise ALREADY_CURRENT
            is_remote_conflict = diff_result["conflict"]
            assert diff_result["diffversion"] == 1
            diff = diff_result["diff"]
            current_remote_rev = diff_result["current"]

            # do not sync if the conflict is remote and local, or if it is local
            # and the page has never been syncronised
            if (wikiutil.containsConflictMarker(current_page.get_raw_body())
                and (remote_rev is None or is_remote_conflict)):
                self.log_status(ActionClass.WARN, _("Skipped page %(pagename)s because of a locally or remotely unresolved conflict.") % {"pagename": local_pagename})
                continue

            if remote_rev is None: # set the remote_rev for the case without any tags
                self.log_status(ActionClass.INFO, _("This is the first synchronisation between this page and the remote wiki."))
                remote_rev = current_remote_rev

            new_contents = patch(old_contents, decompress(diff)).decode("utf-8")
            old_contents = old_contents.encode("utf-8")

            # here, the actual merge happens
            verynewtext = diff3.text_merge(old_contents, new_contents, current_page.get_raw_body(), 2, *conflict_markers)

            new_local_rev = current_rev + 1 # XXX commit first?
            local_full_iwid = packLine([local.get_iwid(), local.get_interwiki_name()])
            remote_full_iwid = packLine([remote.get_iwid(), remote.get_interwiki_name()])

            diff = textdiff(new_contents.encode("utf-8"), verynewtext.encode("utf-8"))
            very_current_remote_rev = remote.merge_diff(rp.remote_name, compress(diff), new_local_rev, remote_rev, current_remote_rev, local_full_iwid)
            comment = u"Local Merge - %r" % (remote.get_interwiki_name() or remote.get_iwid())

            # XXX upgrade to write lock
            try:
                current_page.saveText(verynewtext, current_rev, comment=comment)
            except PageEditor.EditConflict:
                # XXX remote rollback needed
                assert False, "You stumbled on a problem with the current storage system - I cannot lock pages"
            tags.add(remote_wiki=remote_full_iwid, remote_rev=very_current_remote_rev, current_rev=new_local_rev)

            if not wikiutil.containsConflictMarker(verynewtext):
                self.log_status(ActionClass.INFO, _("Page successfully merged."))
            else:
                self.log_status(ActionClass.WARN, _("Page merged with conflicts."))

            # XXX release lock


def execute(pagename, request):
    ActionClass(pagename, request).render()
