# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - utility functions used by the migration scripts

    @copyright: 2005,2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import os, sys, shutil

opj = os.path.join # yes, I am lazy
join = os.path.join


def fatalError(msg):
    """ Exit with error message on fatal errors """
    print "Fatal error:", msg
    print "Stoping"
    sys.exit(1)


def error(msg):
    """ Report minor error and continue """
    print "Error:", msg


def backup(src, dst):
    """ Create a backup of src directory in dst, create empty src

    @param src: source
    @param dst: destination
    """
    print "Create backup of '%s' in '%s'" % (src, dst)

    if not os.path.isdir(src):
        fatalError("can't find '%s'. You must run this script from the directory where '%s' is located." % src)

    try:
        shutil.move(src, dst)
    except:
        fatalError("can't move '%s' to '%s'" % (src, dst))

    try:
        os.mkdir(src)
    except OSError:
        fatalError("can't create '%s'" % src)


def listdir(path):
    """ Return list of files in path, filtering certain files """
    names = [name for name in os.listdir(path)
             if not name.startswith('.') and
             not name.endswith('.pickle') and
             name != 'CVS']
    return names


def makedir(newdir):
    """ Create a directory, if it doesn't exist """
    try:
        os.mkdir(newdir)
    except OSError:
        pass

def copy_dir(dir_from, dir_to):
    """ Copy a complete directory """
    print "%s/ -> %s/" % (dir_from, dir_to)
    try:
        shutil.copytree(dir_from, dir_to)
    except Exception, err:
        error("can't copy '%s' to '%s' (%s)" % (dir_from, dir_to, str(err)))


def copy_file(fname_from, fname_to):
    """ Copy a single file """
    print "%s -> %s" % (fname_from, fname_to)
    try:
        shutil.copy2(fname_from, fname_to) # copies file data, mode, atime, mtime
    except:
        error("can't copy '%s' to '%s'" % (fname_from, fname_to))


def move_file(fname_from, fname_to):
    """ Move a single file """
    print "%s -> %s" % (fname_from, fname_to)
    try:
        shutil.move(fname_from, fname_to) # moves file (even to different filesystem, including mode and atime/mtime)
    except:
        error("can't move '%s' to '%s'" % (fname_from, fname_to))


def copy(items, srcdir, dstdir):
    """ copy items from src dir into dst dir

    @param items: list of items to copy
    @param srcdir: source directory to copy items from
    @param dstdir: destination directory to copy into
    """
    for item in items:
        src = join(srcdir, item)
        dst = join(dstdir, item)

        # Copy directories
        if os.path.isdir(src):
            copy_dir(src, dst)
        elif os.path.isfile(src):
            copy_file(src, dst)
        else:
            error("can't find '%s'" % src)

