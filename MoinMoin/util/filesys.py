# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - File System Utilities

    @copyright: 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import sys, os, shutil, errno
from stat import S_ISDIR, ST_MODE, S_IMODE
from MoinMoin import config

#############################################################################
### Misc Helpers
#############################################################################

def chmod(name, mode, catchexception=True):
    try:
        return os.chmod(name, mode)
    except OSError:
        if not catchexception:
            raise

def makedirs(name, mode=0777):
    """ Super-mkdir; create a leaf directory and all intermediate ones.
    
    Works like mkdir, except that any intermediate path segment (not
    just the rightmost) will be created if it does not exist.  This is
    recursive.

    This is modified version of the os.makedirs from Python 2.4. We add
    explicit chmod call after the mkdir call. Fixes some practical
    permission problems on Linux.
    """
    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    if head and tail and not os.path.exists(head):
        makedirs(head, mode)
        if tail == os.curdir: # xxx/newdir/. exists if xxx/newdir exists
            return
    try:
        os.mkdir(name, mode & config.umask)
    except OSError, err:
        if err.errno != errno.EEXIST:
            raise
    else:
        os.chmod(name, mode & config.umask)

# The original function name is used because it's a modified function
makeDirs = makedirs


def rename(oldname, newname):
    ''' Multiplatform rename

    Needed because win32 rename is not POSIX compliant, and does not
    remove target file if it exists.

    Problem: this "rename" is not atomic any more on win32.

    FIXME: What about rename locking? we can have a lock file in the
    page directory, named: PageName.lock, and lock this file before we
    rename, then unlock when finished.
    '''
    if os.name == 'nt':
        if os.path.isfile(newname):
            try:
                os.remove(newname)
            except OSError, er:
                pass # let os.rename give us the error (if any)
    return os.rename(oldname, newname)


def copystat(src, dst):
    """Copy stat bits from src to dst

    This should be used when shutil.copystat would be used on directories
    on win32 because win32 does not support utime() for directories.

    According to the official docs written by Microsoft, it returns ENOACCES if the
    supplied filename is a directory. Looks like a trainee implemented the function.
    """
    if sys.platform == 'win32' and S_ISDIR(os.stat(dst)[ST_MODE]):
        if os.name == 'nt':
            st = os.stat(src)
            mode = S_IMODE(st[ST_MODE])
            if hasattr(os, 'chmod'):
                os.chmod(dst, mode)
        #else: pass # we are on Win9x,ME - no chmod here
    else:
        shutil.copystat(src, dst)


def copytree(src, dst, symlinks=False):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    In contrary to shutil.copytree, this version also copies directory
    stats, not only file stats.

    """
    names = os.listdir(src)
    os.mkdir(dst)
    copystat(src,dst)
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks)
            else:
                shutil.copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error), why:
            errors.append((srcname, dstname, why))
    if errors:
        raise EnvironmentError, errors

# Code could come from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65203

# we currently do not support locking
LOCK_EX = LOCK_SH = LOCK_NB = 0

def lock(file, flags):
    raise NotImplementedError

def unlock(file):
    raise NotImplementedError


# ----------------------------------------------------------------------
# Get real case of path name on case insensitive file systems
# TODO: nt version?

if sys.platform == 'darwin':

    def realPathCase(path):
        """ Return the real case of path e.g. PageName for pagename

        HFS and HFS+ file systems, are case preserving but case
        insensitive. You can't have 'file' and 'File' in the same
        directory, but you can get the real name of 'file'.
        
        @param path: string
        @rtype: string
        @return the real case of path or None
        """
        try:
            from Carbon import File
            return File.FSRef(path).as_pathname()
        except (ImportError, File.Error):
            return None

else:

    def realPathCase(path):
        return None
