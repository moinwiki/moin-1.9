# -*- coding: iso-8859-1 -*-
"""
    MoinMoin caching module

    @copyright: 2001-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os
import warnings

# cPickle can encode normal and Unicode strings
# see http://docs.python.org/lib/node66.html
try:
    import cPickle as pickle
except ImportError:
    import pickle

# Set pickle protocol, see http://docs.python.org/lib/node64.html
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL

from MoinMoin import config
from MoinMoin.util import filesys, lock

# filter the tempname warning because we create the tempfile only in directories
# where only we should have write access initially
warnings.filterwarnings("ignore", "tempnam.*security", RuntimeWarning, "MoinMoin.caching")

class CacheError(Exception):
    """ raised if we have trouble reading or writing to the cache """
    pass

class CacheEntry:
    def __init__(self, request, arena, key, scope='page_or_wiki', do_locking=True, use_pickle=False):
        """ init a cache entry
            @param request: the request object
            @param arena: either a string or a page object, when we want to use
                          page local cache area
            @param key: under which key we access the cache content
            @param lock: if there should be a lock, normally True
            @param scope: the scope where we are caching:
                          'item' - an item local cache
                          'wiki' - a wiki local cache
                          'farm' - a cache for the whole farm
        """
        self.request = request
        self.key = key
        self.locking = do_locking
        self.use_pickle = use_pickle
        if scope == 'page_or_wiki': # XXX DEPRECATED, remove later
            if isinstance(arena, str):
                self.arena_dir = os.path.join(request.cfg.cache_dir, request.cfg.siteid, arena)
            else: # arena is in fact a page object
                self.arena_dir = arena.getPagePath('cache', check_create=1)
        elif scope == 'item': # arena is a Page instance
            # we could move cache out of the page directory and store it to cache_dir
            self.arena_dir = arena.getPagePath('cache', check_create=1)
        elif scope == 'wiki':
            self.arena_dir = os.path.join(request.cfg.cache_dir, request.cfg.siteid, arena)
        elif scope == 'farm':
            self.arena_dir = os.path.join(request.cfg.cache_dir, '__common__', arena)
        if not os.path.exists(self.arena_dir):
            os.makedirs(self.arena_dir)
        if self.locking:
            self.lock_dir = os.path.join(self.arena_dir, '__lock__')
            self.rlock = lock.LazyReadLock(self.lock_dir, 60.0)
            self.wlock = lock.LazyWriteLock(self.lock_dir, 60.0)

    def _filename(self):
        return os.path.join(self.arena_dir, self.key)

    def _tmpfilename(self):
        return os.tempnam(self.arena_dir, self.key)

    def exists(self):
        return os.path.exists(self._filename())

    def mtime(self):
        try:
            return os.path.getmtime(self._filename())
        except (IOError, OSError):
            return 0

    def needsUpdate(self, filename, attachdir=None):
        if not self.exists():
            return 1

        try:
            ctime = os.path.getmtime(self._filename())
            ftime = os.path.getmtime(filename)
        except os.error:
            return 1

        needsupdate = ftime > ctime

        # if a page depends on the attachment dir, we check this, too:
        if not needsupdate and attachdir:
            try:
                ftime2 = os.path.getmtime(attachdir)
            except os.error:
                ftime2 = 0
            needsupdate = ftime2 > ctime

        return needsupdate

    def copyto(self, filename):
        # currently unused function
        import shutil
        tmpfname = self._tmpfilename()
        fname = self._filename()
        if not self.locking or self.locking and self.wlock.acquire(1.0):
            try:
                shutil.copyfile(filename, tmpfname)
                # this is either atomic or happening with real locks set:
                filesys.rename(tmpfname, fname)
            finally:
                if self.locking:
                    self.wlock.release()
        else:
            self.request.log("Can't acquire write lock in %s" % self.lock_dir)

    def update(self, content):
        try:
            tmpfname = self._tmpfilename()
            fname = self._filename()
            if self.use_pickle:
                content = pickle.dumps(content, PICKLE_PROTOCOL)
            if not self.locking or self.locking and self.wlock.acquire(1.0):
                try:
                    # we do not write content to old inode, but to a new file
                    # se we don't need to lock when we just want to read the file
                    # (at least on POSIX, this works)
                    f = open(tmpfname, 'wb')
                    f.write(content)
                    f.close()
                    # this is either atomic or happening with real locks set:
                    filesys.rename(tmpfname, fname)
                finally:
                    if self.locking:
                        self.wlock.release()
            else:
                self.request.log("Can't acquire write lock in %s" % self.lock_dir)
        except (pickle.PicklingError, IOError, ValueError), err:
            raise CacheError(str(err))

    def remove(self):
        if not self.locking or self.locking and self.wlock.acquire(1.0):
            try:
                try:
                    os.remove(self._filename())
                except OSError:
                    pass
            finally:
                if self.locking:
                    self.wlock.release()
        else:
            self.request.log("Can't acquire write lock in %s" % self.lock_dir)

    def content(self):
        try:
            if not self.locking or self.locking and self.rlock.acquire(1.0):
                try:
                    f = open(self._filename(), 'rb')
                    data = f.read()
                    f.close()
                finally:
                    if self.locking:
                        self.rlock.release()
            else:
                self.request.log("Can't acquire read lock in %s" % self.lock_dir)
            if self.use_pickle:
                data = pickle.loads(data)
            return data
        except (pickle.UnpicklingError, IOError, EOFError, ValueError), err:
            raise CacheError(str(err))

