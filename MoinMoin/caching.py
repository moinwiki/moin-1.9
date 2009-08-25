# -*- coding: iso-8859-1 -*-
"""
    MoinMoin caching module

    @copyright: 2001-2004 by Juergen Hermann <jh@web.de>,
                2006-2008 MoinMoin:ThomasWaldmann,
                2008 MoinMoin:ThomasPfaff
    @license: GNU GPL, see COPYING for details.
"""

import os
import shutil
import tempfile

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config
from MoinMoin.util import filesys, lock, pickle, PICKLE_PROTOCOL


class CacheError(Exception):
    """ raised if we have trouble reading or writing to the cache """
    pass


def get_arena_dir(request, arena, scope):
    if scope == 'item': # arena is a Page instance
        # we could move cache out of the page directory and store it to cache_dir
        return arena.getPagePath('cache', check_create=1)
    elif scope == 'wiki':
        return os.path.join(request.cfg.cache_dir, request.cfg.siteid, arena)
    elif scope == 'farm':
        return os.path.join(request.cfg.cache_dir, '__common__', arena)
    return None


def get_cache_list(request, arena, scope):
    arena_dir = get_arena_dir(request, arena, scope)
    try:
        return filesys.dclistdir(arena_dir)
    except OSError:
        return []


class CacheEntry:
    def __init__(self, request, arena, key, scope='wiki', do_locking=True,
                 use_pickle=False, use_encode=False):
        """ init a cache entry
            @param request: the request object
            @param arena: either a string or a page object, when we want to use
                          page local cache area
            @param key: under which key we access the cache content
            @param scope: the scope where we are caching:
                          'item' - an item local cache
                          'wiki' - a wiki local cache
                          'farm' - a cache for the whole farm
            @param do_locking: if there should be a lock, normally True
            @param use_pickle: if data should be pickled/unpickled (nice for arbitrary cache content)
            @param use_encode: if data should be encoded/decoded (nice for readable cache files)
        """
        self.request = request
        self.key = key
        self.locking = do_locking
        self.use_pickle = use_pickle
        self.use_encode = use_encode
        self.arena_dir = get_arena_dir(request, arena, scope)
        if not os.path.exists(self.arena_dir):
            os.makedirs(self.arena_dir)
        self._fname = os.path.join(self.arena_dir, key)

        if self.locking:
            self.lock_dir = os.path.join(self.arena_dir, '__lock__')
            self.rlock = lock.LazyReadLock(self.lock_dir, 60.0)
            self.wlock = lock.LazyWriteLock(self.lock_dir, 60.0)

        # used by file-like api:
        self._lock = None  # either self.rlock or self.wlock
        self._fileobj = None  # open cache file object
        self._tmp_fname = None  # name of temporary file (used for write)
        self._mode = None  # mode of open file object


    def _filename(self):
        # DEPRECATED - please use file-like api
        return self._fname

    def exists(self):
        return os.path.exists(self._fname)

    def mtime(self):
        # DEPRECATED for checking a changed on-disk cache, please use
        # self.uid() for this, see below
        try:
            return os.path.getmtime(self._fname)
        except (IOError, OSError):
            return 0

    def size(self):
        try:
            return os.path.getsize(self._fname)
        except (IOError, OSError):
            return 0

    def uid(self):
        """ Return a value that likely changes when the on-disk cache was updated.

            See docstring of MoinMoin.util.filesys.fuid for details.
        """
        return filesys.fuid(self._fname)

    def needsUpdate(self, filename, attachdir=None):
        # following code is not necessary. will trigger exception and give same result
        #if not self.exists():
        #    return 1

        try:
            ctime = os.path.getmtime(self._fname)
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

    def _determine_locktype(self, mode):
        """ return the correct lock object for a specific file access mode """
        if self.locking:
            if 'r' in mode:
                lock = self.rlock
            if 'w' in mode or 'a' in mode:
                lock = self.wlock
        else:
            lock = None
        return lock

    # file-like interface ----------------------------------------------------

    def open(self, filename=None, mode='r', bufsize=-1):
        """ open the cache for reading/writing

        @param filename: must be None (default - automatically determine filename)
        @param mode: 'r' (read, default), 'w' (write)
                     Note: if mode does not include 'b' (binary), it will be
                           automatically changed to include 'b'.
        @param bufsize: size of read/write buffer (default: -1 meaning automatic)
        @return: None (the opened file object is kept in self._fileobj and used
                 implicitely by read/write/close functions of CacheEntry object.
        """
        assert self._fileobj is None, 'caching: trying to open an already opened cache'
        assert filename is None, 'caching: giving a filename is not supported (yet?)'

        self._lock = self._determine_locktype(mode)

        if 'b' not in mode:
            mode += 'b'  # we want to use binary mode, ever!
        self._mode = mode  # for self.close()

        if not self.locking or self.locking and self._lock.acquire(1.0):
            try:
                if 'r' in mode:
                    self._fileobj = open(self._fname, mode, bufsize)
                elif 'w' in mode:
                    # we do not write content to old inode, but to a new file
                    # so we don't need to lock when we just want to read the file
                    # (at least on POSIX, this works)
                    fd, self._tmp_fname = tempfile.mkstemp('.tmp', self.key, self.arena_dir)
                    self._fileobj = os.fdopen(fd, mode, bufsize)
                else:
                    raise ValueError("caching: mode does not contain 'r' or 'w'")
            finally:
                if self.locking:
                    self._lock.release()
                    self._lock = None
        else:
            logging.error("Can't acquire read/write lock in %s" % self.lock_dir)


    def read(self, size=-1):
        """ read data from cache file

        @param size: how many bytes to read (default: -1 == everything)
        @return: read data (str)
        """
        return self._fileobj.read(size)

    def write(self, data):
        """ write data to cache file

        @param data: write data (str)
        """
        self._fileobj.write(data)

    def close(self):
        """ close cache file (and release lock, if any) """
        if self._fileobj:
            self._fileobj.close()
            self._fileobj = None
            if 'w' in self._mode:
                filesys.chmod(self._tmp_fname, 0666 & config.umask) # fix mode that mkstemp chose
                # this is either atomic or happening with real locks set:
                filesys.rename(self._tmp_fname, self._fname)

        if self._lock:
            if self.locking:
                self._lock.release()
            self._lock = None

    # ------------------------------------------------------------------------

    def update(self, content):
        try:
            if hasattr(content, 'read'):
                # content is file-like
                assert not (self.use_pickle or self.use_encode), 'caching: use_pickle and use_encode not supported with file-like api'
                try:
                    self.open(mode='w')
                    shutil.copyfileobj(content, self)
                finally:
                    self.close()
            else:
                # content is a string
                if self.use_pickle:
                    content = pickle.dumps(content, PICKLE_PROTOCOL)
                elif self.use_encode:
                    content = content.encode(config.charset)

                try:
                    self.open(mode='w')
                    self.write(content)
                finally:
                    self.close()
        except (pickle.PicklingError, OSError, IOError, ValueError), err:
            raise CacheError(str(err))

    def content(self):
        # no file-like api yet, we implement it when we need it
        try:
            try:
                self.open(mode='r')
                data = self.read()
            finally:
                self.close()
            if self.use_pickle:
                data = pickle.loads(data)
            elif self.use_encode:
                data = data.decode(config.charset)
            return data
        except (pickle.UnpicklingError, IOError, EOFError, ValueError), err:
            raise CacheError(str(err))

    def remove(self):
        if not self.locking or self.locking and self.wlock.acquire(1.0):
            try:
                try:
                    os.remove(self._fname)
                except OSError:
                    pass
            finally:
                if self.locking:
                    self.wlock.release()
        else:
            logging.error("Can't acquire write lock in %s" % self.lock_dir)


