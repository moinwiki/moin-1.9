#!/usr/bin/env python
"""
    migration from moin 1.3 < patch-xxx to moin 1.3 >= patch-xxx
    We fix 2 issues here:
    * we forgot to handle edit-lock files. We simply delete them now.
    * we convert attachment names to utf-8

    Steps for a successful migration:

        1. Stop your wiki and make a backup of old data and code

        2. Make a copy of the wiki's "data" directory to your working dir

        3. make sure that from_encoding and to_encoding matches your needs (see
           beginning of script below and config.charset in moin_config.py) and
           run python2.3 12_to_13_mig10.py from your working dir

        4. If there was no error, you will find:
            data.pre-mig10 - the script renames your data directory copy to that name
            data - converted data dir

        5. Verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed.

        6. Copy additional files from data.pre-mig10 to data (maybe intermaps, logs,
           etc.). Be aware that the file contents AND file names of wiki content
           may have changed, so DO NOT copy the files inside the cache/ directory,
           let the wiki refill it.

        7. Replace the data directory your wiki uses with the data directory
           you created by previous steps. DO NOT simply copy the converted stuff
           into the original or you will duplicate pages and create chaos!

        8. Test it - if something has gone wrong, you still have your backup.


    @copyright: 2005 Thomas Waldmann
    @license: GPL, see COPYING for details
"""

from_encoding = 'iso8859-1'
#from_encoding = 'utf-8'

to_encoding = 'utf-8'

import os, os.path, sys, urllib

# Insert THIS moin dir first into sys path, or you would run another
# version of moin!
sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, move_file, copy_dir

def migrate(dir_to):
    """ this removes edit-lock files from the pagedirs and
        converts attachment filenames
    """
    pagesdir = opj(dir_to, 'pages')
    pagelist = listdir(pagesdir)
    for pagename in pagelist:
        pagedir = opj(pagesdir, pagename)
        editlock = opj(pagedir, 'edit-lock')
        try:
            os.remove(editlock)
        except:
            pass

        attachdir = os.path.join(pagedir, 'attachments')
        for root, dirs, files in os.walk(attachdir):
            for f in  files:
                try:
                    f.decode(to_encoding)
                except UnicodeDecodeError:
                    fnew = f.decode(from_encoding).encode(to_encoding)
                    os.rename(os.path.join(root, f), os.path.join(root, fnew))
                    print 'renamed', f, '\n ->', fnew, ' in dir:', root


origdir = 'data.pre-mig10'
destdir = 'data'

# Backup original dir and create new empty dir
try:
    os.rename(destdir, origdir)
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

copy_dir(origdir, destdir)
migrate(destdir)


