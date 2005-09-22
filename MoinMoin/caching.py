# -*- coding: iso-8859-1 -*-
"""
    MoinMoin caching module

    @copyright: 2001-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os
from MoinMoin import config
from MoinMoin.util import filesys

class CacheEntry:
    def __init__(self, request, arena, key):
        """ init a cache entry
            @param request: the request object
            @param arena: either a string or a page object, when we want to use
                          page local cache area
            @param key: under which key we access the cache content
        """
        if isinstance(arena, str):
            self.arena_dir = os.path.join(request.cfg.cache_dir, arena)
            filesys.makeDirs(self.arena_dir)
        else: # arena is in fact a page object
            cache_dir = None
            self.arena_dir = arena.getPagePath('cache', check_create=1)
        self.key = key

    def _filename(self):
        return os.path.join(self.arena_dir, self.key)

    def exists(self):
        return os.path.exists(self._filename())

    def mtime(self):
        try:
            return os.path.getmtime(self._filename())
        except (IOError, OSError):
            return 0

    def needsUpdate(self, filename, attachdir=None):
        if not self.exists(): return 1

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
        import shutil
        shutil.copyfile(filename, self._filename())

        try:
            os.chmod(self._filename(), 0666 & config.umask)
        except OSError:
            pass

    def update(self, content, encode=False):
        if encode:
            content = content.encode(config.charset)
        open(self._filename(), 'wb').write(content)

        try:
            os.chmod(self._filename(), 0666 & config.umask)
        except OSError:
            pass

    def remove(self):
        try:
            os.remove(self._filename())
        except OSError:
            pass

    def content(self, decode=False):
        data = open(self._filename(), 'rb').read()
        if decode:
            data = data.decode(config.charset)
        return data

