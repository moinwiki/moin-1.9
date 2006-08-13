# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SyncPages action

    This action allows you to synchronise pages of two wikis.

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import os
import re
import xmlrpclib

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
from MoinMoin.wikisync import TagStore, UnsupportedWikiException, SyncPage, MoinLocalWiki, MoinRemoteWiki
from MoinMoin.util.bdiff import decompress, patch, compress, textdiff
from MoinMoin.util import diff3


# directions
UP, DOWN, BOTH = range(3)
directions_map = {"up": UP, "down": DOWN, "both": BOTH}


class ActionStatus(Exception): pass


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

        if params["pageMatch"] is not None:
            params["pageMatch"] = re.compile(params["pageMatch"], re.U)

        # we do not support matching or listing pages if there is a group of pages
        if params["groupList"]:
            params["pageMatch"] = None
            params["pageList"] = None

        return params

    def render(self):
        """ Render action

        This action returns a status message.
        """
        _ = self.request.getText

        params = self.fix_params(self.parse_page())

        try:
            if params["direction"] == UP:
                raise ActionStatus(_("The only supported directions are BOTH and DOWN."))

            if not self.request.cfg.interwikiname:
                raise ActionStatus(_("Please set an interwikiname in your wikiconfig (see HelpOnConfiguration) to be able to use this action."))

            if not params["remoteWiki"]:
                raise ActionStatus(_("Incorrect parameters. Please supply at least the ''remoteWiki'' parameter."))

            local = MoinLocalWiki(self.request, params["localPrefix"], params["pageList"])
            try:
                remote = MoinRemoteWiki(self.request, params["remoteWiki"], params["remotePrefix"], params["pageList"])
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
        direction = params["direction"]

        l_pages = local.get_pages()
        r_pages = remote.get_pages(exclude_non_writable=direction != DOWN)

        if params["groupList"]:
            pages_from_groupList = set(local.getGroupItems(params["groupList"]))
            r_pages = SyncPage.filter(r_pages, pages_from_groupList.__contains__)
            l_pages = SyncPage.filter(l_pages, pages_from_groupList.__contains__)

        m_pages = [elem.add_missing_pagename(local, remote) for elem in SyncPage.merge(l_pages, r_pages)]

        print "Got %i local, %i remote pages, %i merged pages" % (len(l_pages), len(r_pages), len(m_pages)) # XXX remove

        if params["pageMatch"]:
            m_pages = SyncPage.filter(m_pages, params["pageMatch"].match)
        print "After filtering: Got %i merges pages" % (len(m_pages), ) # XXX remove

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
            current_page = PageEditor(self.request, local_pagename) # YYY direct access
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
                if remote_rev == rp.remote_rev and (direction == DOWN or local_rev == current_rev):
                    continue # no changes done, next page
                old_contents = Page(self.request, local_pagename, rev=local_rev).get_raw_body_str() # YYY direct access

            self.log_status(ActionClass.INFO, _("Synchronising page %(pagename)s with remote page %(remotepagename)s ...") % {"pagename": local_pagename, "remotepagename": rp.remote_name})

            if remote_rev != rp.remote_rev:
                diff_result = remote.get_diff(rp.remote_name, remote_rev, None) # XXX might raise ALREADY_CURRENT
                is_remote_conflict = diff_result["conflict"]
                assert diff_result["diffversion"] == 1
                diff = diff_result["diff"]
                current_remote_rev = diff_result["current"]
            else:
                current_remote_rev = remote_rev
                is_remote_conflict = wikiutil.containsConflictMarker(old_contents.decode("utf-8"))
                diff = None

            # do not sync if the conflict is remote and local, or if it is local
            # and the page has never been syncronised
            if (wikiutil.containsConflictMarker(current_page.get_raw_body())
                and (remote_rev is None or is_remote_conflict)):
                self.log_status(ActionClass.WARN, _("Skipped page %(pagename)s because of a locally or remotely unresolved conflict.") % {"pagename": local_pagename})
                continue

            if remote_rev is None: # set the remote_rev for the case without any tags
                self.log_status(ActionClass.INFO, _("This is the first synchronisation between this page and the remote wiki."))
                remote_rev = current_remote_rev

            old_contents_dec = old_contents.decode("utf-8")
            if diff is None:
                new_contents = old_contents_dec
            else:
                new_contents = patch(old_contents, decompress(diff)).decode("utf-8")
            old_contents = old_contents_dec

            # here, the actual merge happens
            print "Merging %r, %r and %r" % (old_contents, new_contents, current_page.get_raw_body())
            verynewtext = diff3.text_merge(old_contents, new_contents, current_page.get_raw_body(), 2, *conflict_markers)

            local_full_iwid = packLine([local.get_iwid(), local.get_interwiki_name()])
            remote_full_iwid = packLine([remote.get_iwid(), remote.get_interwiki_name()])

            diff = textdiff(new_contents.encode("utf-8"), verynewtext.encode("utf-8"))
            #print "Diff against %r" % new_contents.encode("utf-8")

            comment = u"Local Merge - %r" % (remote.get_interwiki_name() or remote.get_iwid())

            # XXX upgrade to write lock
            try:
                current_page.saveText(verynewtext, current_rev, comment=comment) # YYY direct access
            except PageEditor.Unchanged:
                pass
            except PageEditor.EditConflict:
                assert False, "You stumbled on a problem with the current storage system - I cannot lock pages"

            new_local_rev = current_page.get_real_rev()

            try:
                very_current_remote_rev = remote.merge_diff(rp.remote_name, compress(diff), new_local_rev, current_remote_rev, current_remote_rev, local_full_iwid)
            except Exception, e:
                raise # XXX rollback locally
            else:
                tags.add(remote_wiki=remote_full_iwid, remote_rev=very_current_remote_rev, current_rev=new_local_rev)

            if not wikiutil.containsConflictMarker(verynewtext):
                self.log_status(ActionClass.INFO, _("Page successfully merged."))
            else:
                self.log_status(ActionClass.WARN, _("Page merged with conflicts."))

            # XXX release lock


def execute(pagename, request):
    ActionClass(pagename, request).render()
