# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Run Unit tests

Usage:

    runtests [test_name...]

Without arguments run all the tests in the _tests package.

@copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
@license: GNU GPL, see COPYING for details.
"""

import os, sys, shutil, errno, tarfile

moinpath = os.path.join(os.path.dirname(sys.argv[0]), os.pardir)
sys.path.insert(0, os.path.abspath(moinpath))

from MoinMoin import _tests

WIKI = os.path.abspath('testwiki')
SHARE = os.path.abspath('wiki')

def removeTestWiki():
    print 'removing old wiki ...'
    for dir in ['data', 'underlay']:
        try:
            shutil.rmtree(os.path.join(WIKI, dir))
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise

def copyData():
    print 'copying data ...'
    src = os.path.join(SHARE, 'data')
    dst = os.path.join(WIKI, 'data')
    shutil.copytree(src, dst)
    # Remove arch-ids dirs
    for path, dirs, files in os.walk(dst):
        for dir in dirs[:]:
            if dir == '.arch-ids':
                shutil.rmtree(os.path.join(path, dir))
                dirs.remove(dir)


def untarUnderlay():
    print 'untaring underlay ...'
    tar = tarfile.open(os.path.join(SHARE, 'underlay.tar.bz2'), mode='r:bz2')
    for member in tar:
        tar.extract(member, WIKI)
    tar.close()


def run():   
    removeTestWiki()
    copyData()
    untarUnderlay()
    _tests.run(names=sys.argv[1:])


if __name__ == '__main__':
    run()
