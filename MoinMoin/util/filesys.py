# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - File System Utilities

    @copyright: 2002 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import sys, os, shutil, time
from stat import S_ISDIR, ST_MODE, S_IMODE

#############################################################################
### Misc Helpers
#############################################################################

def chmod(name, mode, catchexception=True):
    """ change mode of some file/dir on platforms that support it.
        usually you don't need this because we use os.umask() when importing
        request.py
    """
    try:
        os.chmod(name, mode)
    except OSError:
        if not catchexception:
            raise


def rename(oldname, newname):
    """ Multiplatform rename

    Needed because win32 rename is not POSIX compliant, and does not
    remove target file if it exists.

    Problem: this "rename" is not atomic any more on win32.

    FIXME: What about rename locking? we can have a lock file in the
    page directory, named: PageName.lock, and lock this file before we
    rename, then unlock when finished.
    """
    if os.name == 'nt':
        if os.path.isfile(newname):
            try:
                os.remove(newname)
            except OSError:
                pass # let os.rename give us the error (if any)
    os.rename(oldname, newname)

def touch(name):
    if sys.platform == 'win32':
        import win32file, win32con, pywintypes

        access = win32file.GENERIC_WRITE
        share = (win32file.FILE_SHARE_DELETE |
                 win32file.FILE_SHARE_READ |
                 win32file.FILE_SHARE_WRITE)
        create = win32file.OPEN_EXISTING
        mtime = time.gmtime()
        handle = win32file.CreateFile(name, access, share, None, create,
                                      win32file.FILE_ATTRIBUTE_NORMAL |
                                      win32con.FILE_FLAG_BACKUP_SEMANTICS,
                                      None)
        try:
            newTime = pywintypes.Time(mtime)
            win32file.SetFileTime(handle, newTime, newTime, newTime)
        finally:
            win32file.CloseHandle(handle)
    else:
        os.utime(name, None)


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
                os.chmod(dst, mode) # KEEP THIS ONE!
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
    copystat(src, dst)
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

# dircache stuff seems to be broken on win32 (at least for FAT32, maybe NTFS)
DCENABLED = 1 # set to 0 to disable dirchache usage
def dcdisable():
    global DCENABLED
    DCENABLED = 0

import dircache

def dclistdir(path):
    if sys.platform == 'win32' or not DCENABLED:
        return os.listdir(path)
    else:
        return dircache.listdir(path)

def dcreset():
    if sys.platform == 'win32' or not DCENABLED:
        return
    else:
        return dircache.reset()
