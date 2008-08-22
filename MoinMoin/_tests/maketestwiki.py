# -*- coding: iso-8859-1 -*-
"""
MoinMoin - make a test wiki

Usage:

    maketestwiki.py

@copyright: 2005 by Thomas Waldmann
@license: GNU GPL, see COPYING for details.
"""

import os, sys, shutil, errno

filename = globals().get("__file__") or sys.argv[0]
moinpath = os.path.abspath(os.path.join(os.path.dirname(filename), os.pardir, os.pardir))

from MoinMoin.support import tarfile

WIKI = os.path.abspath(os.path.join(moinpath, 'tests', 'wiki'))
SHARE = os.path.abspath(os.path.join(moinpath, 'wiki'))


def removeTestWiki():
    print 'removing old wiki ...'
    for dir in ['data', 'underlay']:
        try:
            shutil.rmtree(os.path.join(WIKI, dir))
        except OSError, err:
            if not (err.errno == errno.ENOENT or
                    (err.errno == 3 and os.name == 'nt')):
                raise


def copyData():
    print 'copying data ...'
    src = os.path.join(SHARE, 'data')
    dst = os.path.join(WIKI, 'data')
    shutil.copytree(src, dst)


def untarUnderlay():
    print 'untaring underlay ...'
    tar = tarfile.open(os.path.join(SHARE, 'underlay.tar'))
    for member in tar:
        tar.extract(member, WIKI)
    tar.close()


def run(skip_if_existing=False):
    try:
        os.makedirs(WIKI)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

    if skip_if_existing and os.path.exists(os.path.join(WIKI, 'data')):
        return
    removeTestWiki()
    copyData()
    untarUnderlay()

if __name__ == '__main__':
    sys.path.insert(0, moinpath)
    run()

