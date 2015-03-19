# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Synchronisation

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import os
import socket
import xmlrpclib

from MoinMoin import wikiutil
from MoinMoin.util import lock, pickle
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.packages import unpackLine, packLine


MIMETYPE_MOIN = "text/wiki"
# sync directions
UP, DOWN, BOTH = range(3)


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


class UnsupportedWikiException(Exception):
    pass


class NotAllowedException(Exception):
    pass


class SyncPage(object):
    """ This class represents a page in one or two wiki(s). """
    def __init__(self, name, local_rev=None, remote_rev=None, local_name=None, remote_name=None,
                 local_deleted=False, remote_deleted=False):
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
        self.local_deleted = local_deleted
        self.remote_deleted = remote_deleted
        self.local_mime_type = MIMETYPE_MOIN   # XXX no usable storage API yet
        self.remote_mime_type = MIMETYPE_MOIN
        assert remote_rev != 99999999

    def __repr__(self):
        return repr("<Sync Page %r>" % unicode(self))

    def __unicode__(self):
        return u"%s[%s|%s]<%r:%r>" % (self.name, self.local_name, self.remote_name, self.local_rev, self.remote_rev)

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        """ Ensures that the hash value of this page only depends on the canonical name. """
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, SyncPage):
            return False
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
            self.remote_name = (remote.prefix or "") + n_name

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
                d[sp].remote_deleted = sp.remote_deleted
                # XXX merge mime type here
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

    def get_pages(self, **kw):
        """ Returns a list of SyncPage instances. """
        return NotImplemented


class MoinRemoteWiki(RemoteWiki):
    """ Used for MoinMoin wikis reachable via XMLRPC. """
    def __init__(self, request, interwikiname, prefix, pagelist, user, password, verbose=False):
        self.request = request
        self.prefix = prefix
        self.pagelist = pagelist
        self.verbose = verbose
        _ = self.request.getText

        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_interwiki(self.request, interwikiname, '')
        self.wiki_url = wikiutil.mapURL(self.request, wikiurl)
        self.valid = not wikitag_bad
        self.xmlrpc_url = str(self.wiki_url + "?action=xmlrpc2")
        if not self.valid:
            self.connection = None
            return

        self.connection = self.createConnection()

        try:
            iw_list = self.connection.interwikiName()
        except socket.error:
            raise UnsupportedWikiException(_("The wiki is currently not reachable."))
        except xmlrpclib.Fault, err:
            raise UnsupportedWikiException("xmlrpclib.Fault: %s" % str(err))

        if user and password:
            token = self.connection.getAuthToken(user, password)
            if token:
                self.token = token
            else:
                raise NotAllowedException(_("Invalid username or password."))
        else:
            self.token = None

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
        return xmlrpclib.ServerProxy(self.xmlrpc_url, allow_none=True, verbose=self.verbose)

    # Public methods
    def get_diff_pre(self, pagename, from_rev, to_rev, n_name=None):
        """ Returns the binary diff of the remote page named pagename, given
            from_rev and to_rev. Generates the call. """
        return "getDiff", (pagename, from_rev, to_rev, n_name)

    def get_diff_post(self, value):
        """ Processes the return value of the call generated by get_diff_pre. """
        if isinstance(value, xmlrpclib.Fault):
            if value.faultCode == "INVALID_TAG":
                return None
            raise value
        value["diff"] = str(value["diff"]) # unmarshal Binary object
        return value

    def merge_diff_pre(self, pagename, diff, local_rev, delta_remote_rev, last_remote_rev, interwiki_name, n_name):
        """ Merges the diff into the page on the remote side. Generates the call. """
        return "mergeDiff", (pagename, xmlrpclib.Binary(diff), local_rev, delta_remote_rev, last_remote_rev, interwiki_name, n_name)

    def merge_diff_post(self, result):
        """ Processes the return value of the call generated by merge_diff_pre.  """
        if isinstance(result, xmlrpclib.Fault):
            if result.faultCode == "NOT_ALLOWED":
                raise NotAllowedException
            raise result
        return result

    def delete_page_pre(self, pagename, last_remote_rev, interwiki_name):
        """ Deletes a remote page. Generates the call. """
        return "mergeDiff", (pagename, None, None, None, last_remote_rev, interwiki_name, None)

    def delete_page_post(self, result):
        """ Processes the return value of the call generated by delete_page_pre. """
        if isinstance(result, xmlrpclib.Fault):
            if result.faultCode == "NOT_ALLOWED":
                return result.faultString
            raise result
        return ""

    def create_multicall_object(self):
        """ Generates an object that can be used like a MultiCall instance. """
        return xmlrpclib.MultiCall(self.connection)

    def prepare_multicall(self):
        """ Can be used to return initial calls that e.g. authenticate the user.
            @return: [(funcname, (arg,+)*]
        """
        if self.token:
            return [("applyAuthToken", (self.token, ))]
        return []

    def delete_auth_token(self):
        if self.token:
            self.connection.deleteAuthToken(self.token)
            self.token = None

    # Methods implementing the RemoteWiki interface

    def get_interwiki_name(self):
        return self.remote_interwikiname

    def get_iwid(self):
        return self.remote_iwid

    def get_pages(self, **kwargs):
        options = {"include_revno": True,
                   "include_deleted": True,
                   "exclude_non_writable": kwargs["exclude_non_writable"],
                   "include_underlay": False,
                   "prefix": self.prefix,
                   "pagelist": self.pagelist,
                   "mark_deleted": True}
        if self.token:
            m = xmlrpclib.MultiCall(self.connection)
            m.applyAuthToken(self.token)
            m.getAllPagesEx(options)
            tokres, pages = m()
        else:
            pages = self.connection.getAllPagesEx(options)
        rpages = []
        for name, revno in pages:
            normalised_name = normalise_pagename(name, self.prefix)
            if normalised_name is None:
                continue
            if abs(revno) != 99999999: # I love sane in-band signalling
                remote_rev = abs(revno)
                remote_deleted = revno < 0
                rpages.append(SyncPage(normalised_name, remote_rev=remote_rev, remote_name=name, remote_deleted=remote_deleted))
        return rpages

    def __repr__(self):
        return "<MoinRemoteWiki wiki_url=%r valid=%r>" % (getattr(self, "wiki_url", Ellipsis), getattr(self, "valid", Ellipsis))


class MoinLocalWiki(RemoteWiki):
    """ Used for the current MoinMoin wiki. """
    def __init__(self, request, prefix, pagelist):
        self.request = request
        self.prefix = prefix
        self.pagelist = pagelist

    def getGroupItems(self, group_list):
        """ Returns all page names that are listed on the page group_list. """
        pages = []
        for group_pagename in group_list:
            pages.extend(request.groups.get(group_pagename, []))
        return [self.createSyncPage(x) for x in pages]

    def createSyncPage(self, page_name):
        normalised_name = normalise_pagename(page_name, self.prefix)
        if normalised_name is None:
            return None
        page = Page(self.request, page_name)
        revno = page.get_real_rev()
        if revno == 99999999: # I love sane in-band signalling
            return None
        return SyncPage(normalised_name, local_rev=revno, local_name=page_name, local_deleted=not page.exists())

    # Public methods:

    # Methods implementing the RemoteWiki interface
    def delete_page(self, pagename, comment):
        page = PageEditor(self.request, pagename)
        try:
            page.deletePage(comment)
        except PageEditor.AccessDenied, (msg, ):
            return msg
        return ""

    def get_interwiki_name(self):
        return self.request.cfg.interwikiname

    def get_iwid(self):
        return self.request.cfg.iwid

    def get_pages(self, **kwargs):
        assert not kwargs
        if self.prefix or self.pagelist:
            def page_filter(name, prefix=(self.prefix or ""), pagelist=self.pagelist):
                n_name = normalise_pagename(name, prefix)
                if not n_name:
                    return False
                if not pagelist:
                    return True
                return n_name in pagelist
        else:
            page_filter = lambda x: True
        pages = []
        for x in self.request.rootpage.getPageList(exists=False, include_underlay=False, filter=page_filter):
            sp = self.createSyncPage(x)
            if sp:
                pages.append(sp)
        return pages

    def __repr__(self):
        return "<MoinLocalWiki>"


# ------------------ Tags ------------------


class Tag(object):
    """ This class is used to store information about merging state. """

    def __init__(self, remote_wiki, remote_rev, current_rev, direction, normalised_name):
        """ Creates a new Tag.

        @param remote_wiki: The identifier of the remote wiki.
        @param remote_rev: The revision number on the remote end.
        @param current_rev: The related local revision.
        @param direction: The direction of the sync, encoded as an integer.
        """
        assert (isinstance(remote_wiki, basestring) and isinstance(remote_rev, int)
                and isinstance(current_rev, int) and isinstance(direction, int)
                and isinstance(normalised_name, basestring))
        self.remote_wiki = remote_wiki
        self.remote_rev = remote_rev
        self.current_rev = current_rev
        self.direction = direction
        self.normalised_name = normalised_name

    def __repr__(self):
        return u"<Tag normalised_pagename=%r remote_wiki=%r remote_rev=%r current_rev=%r>" % (getattr(self, "normalised_name", "UNDEF"), self.remote_wiki, self.remote_rev, self.current_rev)

    def __cmp__(self, other):
        if not isinstance(other, Tag):
            return NotImplemented
        return cmp(self.current_rev, other.current_rev)


class AbstractTagStore(object):
    """ This class is an abstract base class that shows how to implement classes
        that manage the storage of tags. """

    def __init__(self, page):
        """ Subclasses don't need to call this method. It is just here to enforce
        them having accept a page argument at least. """
        pass

    def dump(self):
        """ Returns all tags for a given item as a string. """
        return repr(self.get_all_tags())

    def add(self, **kwargs):
        """ Adds a Tag object to the current TagStore. """
        print "Got tag for page %r: %r" % (self.page, kwargs)
        return NotImplemented

    def get_all_tags(self):
        """ Returns a list of all Tag objects associated to this page. """
        return NotImplemented

    def get_last_tag(self):
        """ Returns the newest tag. """
        return NotImplemented

    def clear(self):
        """ Removes all tags. """
        return NotImplemented

    def fetch(self, iwid_full=None, direction=None):
        """ Fetches tags by a special IWID or interwiki name. """
        return NotImplemented


class PickleTagStore(AbstractTagStore):
    """ This class manages the storage of tags in pickle files. """

    def __init__(self, page):
        """ Creates a new TagStore that uses pickle files.

        @param page: a Page object where the tags should be related to
        """

        self.page = page
        self.filename = page.getPagePath('synctags', use_underlay=0, check_create=1, isfile=1)
        lock_dir = os.path.join(page.getPagePath('cache', use_underlay=0, check_create=1), '__taglock__')
        self.rlock = lock.ReadLock(lock_dir, 60.0)
        self.wlock = lock.WriteLock(lock_dir, 60.0)

        if not self.rlock.acquire(3.0):
            raise EnvironmentError("Could not lock in PickleTagStore")
        try:
            self.load()
        finally:
            self.rlock.release()

    def load(self):
        """ Loads the tags from the data file. """
        try:
            datafile = file(self.filename, "rb")
            self.tags = pickle.load(datafile)
        except (IOError, EOFError):
            self.tags = []
        else:
            datafile.close()

    def commit(self):
        """ Writes the memory contents to the data file. """
        datafile = file(self.filename, "wb")
        pickle.dump(self.tags, datafile, pickle.HIGHEST_PROTOCOL)
        datafile.close()

    # public methods ---------------------------------------------------
    def add(self, **kwargs):
        if not self.wlock.acquire(3.0):
            raise EnvironmentError("Could not lock in PickleTagStore")
        try:
            self.load()
            self.tags.append(Tag(**kwargs))
            self.commit()
        finally:
            self.wlock.release()

    def get_all_tags(self):
        return self.tags[:]

    def get_last_tag(self):
        temp = self.tags[:]
        temp.sort()
        if not temp:
            return None
        return temp[-1]

    def clear(self):
        self.tags = []
        if not self.wlock.acquire(3.0):
            raise EnvironmentError("Could not lock in PickleTagStore")
        try:
            self.commit()
        finally:
            self.wlock.release()

    def fetch(self, iwid_full, direction=None):
        iwid_full = unpackLine(iwid_full)
        matching_tags = []
        for t in self.tags:
            t_iwid_full = unpackLine(t.remote_wiki)
            if ((t_iwid_full[0] == iwid_full[0]) # either match IWID or IW name
                or (len(t_iwid_full) == 2 and len(iwid_full) == 2 and t_iwid_full[1] == iwid_full[1])
                ) and (direction is None or t.direction == direction):
                matching_tags.append(t)
        return matching_tags


# currently we just have one implementation, so we do not need
# a factory method
TagStore = PickleTagStore

