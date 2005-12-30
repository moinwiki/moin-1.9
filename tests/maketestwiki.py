# -*- coding: iso-8859-1 -*-
"""
MoinMoin - make a test wiki

Usage:

    maketestwiki.py

@copyright: 2005 by Thomas Waldmann
@license: GNU GPL, see COPYING for details.
"""

import os, sys, shutil, errno, tarfile

moinpath = os.path.join(os.path.dirname(sys.argv[0]), os.pardir)
sys.path.insert(0, os.path.abspath(moinpath))

WIKI = os.path.abspath('testwiki')
SHARE = os.path.abspath('wiki')

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
    try:
        os.makedirs(WIKI)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

    removeTestWiki()
    copyData()
    untarUnderlay()

if __name__ == '__main__':
    run()

