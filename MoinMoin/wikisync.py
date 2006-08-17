# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Synchronisation

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import os

try:
    import cPickle as pickle
except ImportError:
    import pickle

from MoinMoin.util import lock
from MoinMoin.packages import unpackLine


class Tag(object):
    """ This class is used to store information about merging state. """
    
    def __init__(self, remote_wiki, remote_rev, current_rev):
        """ Creates a new Tag.
        
        @param remote_wiki: The identifier of the remote wiki.
        @param remote_rev: The revision number on the remote end.
        @param current_rev: The related local revision.
        """
        self.remote_wiki = remote_wiki
        self.remote_rev = remote_rev
        self.current_rev = current_rev

    def __repr__(self):
        return u"<Tag remote_wiki=%r remote_rev=%r current_rev=%r>" % (self.remote_wiki, self.remote_rev, self.current_rev)

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

    def add(self, **kwargs):
        """ Adds a Tag object to the current TagStore. """
        print "Got tag for page %r: %r" % (self.page, kwargs)
        return NotImplemented

    def get_all_tags(self):
        """ Returns a list of all Tag objects associated to this page. """
        return NotImplemented
    
    def clear(self):
        """ Removes all tags. """
        return NotImplemented

    def fetch(self, iwid_full=None, iw_name=None):
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
        self.load()

    def load(self):
        """ Loads the tags from the data file. """
        if not self.rlock.acquire(3.0):
            raise EnvironmentError("Could not lock in PickleTagStore")
        try:
            try:
                datafile = file(self.filename, "rb")
            except IOError:
                self.tags = []
            else:
                self.tags = pickle.load(datafile)
                datafile.close()
        finally:
            self.rlock.release()
    
    def commit(self):
        """ Writes the memory contents to the data file. """
        if not self.wlock.acquire(3.0):
            raise EnvironmentError("Could not lock in PickleTagStore")
        try:
            datafile = file(self.filename, "wb")
            pickle.dump(self.tags, datafile, protocol=pickle.HIGHEST_PROTOCOL)
            datafile.close()
        finally:
            self.wlock.release()

    # public methods ---------------------------------------------------
    def add(self, **kwargs):
        self.tags.append(Tag(**kwargs))
        self.commit()
    
    def get_all_tags(self):
        return self.tags

    def clear(self):
        self.tags = []
        self.commit()

    def fetch(self, iwid_full=None, iw_name=None):
        assert iwid_full ^ iw_name
        if iwid_full:
            iwid_full = unpackLine(iwid_full)
            if len(iwid_full) == 1:
                assert False, "This case is not supported yet" # XXX
            iw_name = iwid_full[1]

        return [t for t in self.tags if t.remote_wiki == iw_name]


# currently we just have one implementation, so we do not need
# a factory method
TagStore = PickleTagStore