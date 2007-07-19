#!/usr/bin/env python
"""
    12_to_13.py - converting CRLF / LF style to the future standard
    Use this to convert from 1.3 pre patch-275 to patch-275.

    Changes:
    * use OS style for logs (== no change, same as it was)
    * use CRLF for page files on any platform (text/* mandates it!) -
      and we will use that MIME type soon.
    * use LF only internally in moin, convert from/to CRLF early/late
      where needed

    @copyright: 2004 Thomas Waldmann
    @license: GPL, see COPYING for details
"""

import os.path, sys, urllib

# Insert THIS moin dir first into sys path, or you would run another
# version of moin!
sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, move_file, copy_dir

def tocrlf(fni, fno):
    """ rewrite a text file using CRLF for line endings, no matter what
        it was before.
    """
    fi = open(fni, "rb")
    data = fi.read()
    fi.close()
    data = data.replace("\r", "")
    lines = data.split("\n")
    data = "\r\n".join(lines)
    if data[-2:] != "\r\n":
        data += "\r\n"
    fo = open(fno, "wb")
    fo.write(data)
    fo.close()
    st = os.stat(fni)
    os.utime(fno, (st.st_atime, st.st_mtime))

def process_pagedirs(dir_from, dir_to):
    pagelist = listdir(dir_from)
    for pagename in pagelist:
        pagedir_from = opj(dir_from, pagename)
        pagedir_to = opj(dir_to, pagename)

        # first we copy all, even the stuff we convert later:
        copy_dir(pagedir_from, pagedir_to)

        rev_from = opj(pagedir_from, 'revisions')
        rev_to = opj(pagedir_to, 'revisions')
        if os.path.exists(rev_from):
            revlist = listdir(rev_from)
            for rfile in revlist:
                rev = int(rfile)
                r_from = opj(rev_from, rfile)
                r_to = opj(rev_to, rfile)
                tocrlf(r_from, r_to)

origdir = 'data.pre-mig7'

try:
    os.rename('data', origdir)
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

os.makedirs(opj('data', 'pages'))

process_pagedirs(opj(origdir, 'pages'), opj('data', 'pages'))

copy_dir(opj(origdir, 'plugin'), opj('data', 'plugin'))

copy_dir(opj(origdir, 'user'), opj('data', 'user'))

copy_file(opj(origdir, 'edit-log'), opj('data', 'edit-log'))
copy_file(opj(origdir, 'event-log'), opj('data', 'event-log'))

copy_file(opj(origdir, 'intermap.txt'), opj('data', 'intermap.txt'))



