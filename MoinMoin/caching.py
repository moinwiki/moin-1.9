# -*- coding: iso-8859-1 -*-
"""
    MoinMoin caching module

    @copyright: 2001-2004 by Juergen Hermann <jh@web.de>,
                2006-2008 MoinMoin:ThomasWaldmann,
                2008 MoinMoin:ThomasPfaff
    @license: GNU GPL, see COPYING for details.
"""

import os
import tempfile

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config
from MoinMoin.util import filesys, lock, pickle, PICKLE_PROTOCOL


class CacheError(Exception):
    """ raised if we have trouble reading or writing to the cache """
    pass


def get_arena_dir(request, arena, scope):
    if scope == 'page_or_wiki': # XXX DEPRECATED, remove later
        if isinstance(arena, str):
            return os.path.join(request.cfg.cache_dir, request.cfg.siteid, arena)
        else: # arena is in fact a page object
            return arena.getPagePath('cache', check_create=1)
    elif scope == 'item': # arena is a Page instance
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
    def __init__(self, request, arena, key, scope='page_or_wiki', do_locking=True,
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
        if self.locking:
            self.lock_dir = os.path.join(self.arena_dir, '__lock__')
            self.rlock = lock.LazyReadLock(self.lock_dir, 60.0)
            self.wlock = lock.LazyWriteLock(self.lock_dir, 60.0)
        # used by file-like api:
        self._fileobj = None
        self._lock = None

    def _filename(self):
        return os.path.join(self.arena_dir, self.key)

    def exists(self):
        return os.path.exists(self._filename())

    def mtime(self):
        # DEPRECATED for checking a changed on-disk cache, please use
        # self.uid() for this, see below
        try:
            return os.path.getmtime(self._filename())
        except (IOError, OSError):
            return 0

    def uid(self):
        """ Return a value that likely changes when the on-disk cache was updated.

            See docstring of MoinMoin.util.filesys.fuid for details.
        """
        return filesys.fuid(self._filename())

    def needsUpdate(self, filename, attachdir=None):
        # following code is not necessary. will trigger exception and give same result
        #if not self.exists():
        #    return 1

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

#    def copyto(self, filename):
#        # currently unused function
#        import shutil
#        tmpfname = self._tmpfilename()
#        fname = self._filename()
#        if not self.locking or self.locking and self.wlock.acquire(1.0):
#            try:
#                shutil.copyfile(filename, tmpfname)
#                # this is either atomic or happening with real locks set:
#                filesys.rename(tmpfname, fname)
#            finally:
#                if self.locking:
#                    self.wlock.release()
#        else:
#            logging.error("Can't acquire write lock in %s" % self.lock_dir)

    def _determine_locktype(self, mode):
        """ return the correct lock object for a specific file access mode """
        if 'r' in mode:
            lock = self.rlock
        if 'w' in mode or 'a' in mode:
            lock = self.wlock
        return lock

    # file-like interface ----------------------------------------------------

    def open(self, filename=None, mode='r', bufsize=-1):
        """ open the cache file for reading/writing

        @param filename: should be None (default - means to use self._filename())
        @param mode: 'r' (read, default), 'w' (write), 'a' (append)
                     Note: if mode does not include 'b' (binary), it will be
                           automatically changed to include 'b'.
        @param bufsize: size of read/write buffer (default: -1 meaning automatic)
        @return: None (the opened file object is kept in self._fileobj and used
                 implicitely by read/write/close functions of CacheEntry object.
        """
        if self._fileobj:
            # bug-possibility: this doesn't check, if there is any lock on the file
            # we assume this, as the first call to open should
            # acquire the lock.
            return

        if filename is None:
            filename = self._filename()
        else:
            raise Exception('caching: giving a filename is not supported (yet?)')

        self._lock = self._determine_locktype(mode)

        if 'b' not in mode:
            mode += 'b'  # we want to use binary mode, ever!

        if not self.locking or self.locking and self._lock.acquire(1.0):
            try:
                self._fileobj = open(filename, mode, bufsize)
            except IOError:
                if self.locking:
                    self._lock.release()
                    self._lock = None
                logging.error("Can't open cache file %s" % filename)
                raise
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

        if self._lock:
            if self.locking:
                self._lock.release()
            self._lock = None

    # ------------------------------------------------------------------------

    def update(self, content):
        try:
            fname = self._filename()
            if self.use_pickle:
                content = pickle.dumps(content, PICKLE_PROTOCOL)
            elif self.use_encode:
                content = content.encode(config.charset)
            if not self.locking or self.locking and self.wlock.acquire(1.0):
                try:
                    # we do not write content to old inode, but to a new file
                    # so we don't need to lock when we just want to read the file
                    # (at least on POSIX, this works)
                    tmp_handle, tmp_fname = tempfile.mkstemp('.tmp', self.key, self.arena_dir)
                    os.write(tmp_handle, content)
                    os.close(tmp_handle)
                    # this is either atomic or happening with real locks set:
                    filesys.rename(tmp_fname, fname)
                    filesys.chmod(fname, 0666 & config.umask) # fix mode that mkstemp chose
                finally:
                    if self.locking:
                        self.wlock.release()
            else:
                logging.error("Can't acquire write lock in %s" % self.lock_dir)
        except (pickle.PicklingError, OSError, IOError, ValueError), err:
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
            logging.error("Can't acquire write lock in %s" % self.lock_dir)

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
                logging.error("Can't acquire read lock in %s" % self.lock_dir)
            if self.use_pickle:
                data = pickle.loads(data)
            elif self.use_encode:
                data = data.decode(config.charset)
            return data
        except (pickle.UnpicklingError, IOError, EOFError, ValueError), err:
            raise CacheError(str(err))

