#!/usr/bin/env python
"""
    migration from moin 1.2 to moin 1.3
    For 1.3, the plugin module loader needs some __init__.py files.
    Although we supply those files in the new "empty wiki template" in
    wiki/data, many people forgot to update their plugin directories,
    so we do that via this mig script now.

    Steps for a successful migration:

        1. Stop your wiki and make a backup of old data and code

        2. Make a copy of the wiki's "data" directory to your working dir

        3. If there was no error, you will find:
            data.pre-mig11 - the script renames your data directory copy to that name
            data - converted data dir

        4. Copy additional files from data.pre-mig11 to data (maybe intermaps, logs,
           etc.). Be aware that the file contents AND file names of wiki content
           may have changed, so DO NOT copy the files inside the cache/ directory,
           let the wiki refill it.

        5. Replace the data directory your wiki uses with the data directory
           you created by previous steps. DO NOT simply copy the converted stuff
           into the original or you will duplicate pages and create chaos!

        6. Test it - if something has gone wrong, you still have your backup.


    @copyright: 2005 Thomas Waldmann
    @license: GPL, see COPYING for details
"""

import os.path, sys, urllib

# Insert THIS moin dir first into sys path, or you would run another
# version of moin!
sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, move_file, copy_dir, makedir

def migrate(destdir):
    plugindir = opj(destdir, 'plugin')
    makedir(plugindir)
    fname = opj(plugindir, '__init__.py')
    f = open(fname, 'w')
    f.write('''\
# *** Do not remove this! ***
# Although being empty, the presence of this file is important for plugins
# working correctly.
''')
    f.close()
    for d in ['action', 'formatter', 'macro', 'parser', 'processor', 'theme', 'xmlrpc', ]:
        thisdir = opj(plugindir, d)
        makedir(thisdir)
        fname = opj(thisdir, '__init__.py')
        f = open(fname, 'w')
        f.write('''\
# -*- coding: iso-8859-1 -*-

from MoinMoin.util import pysupport

modules = pysupport.getPackageModules(__file__)
''')
        f.close()

origdir = 'data.pre-mig11'
destdir = 'data'

# Backup original dir and create new empty dir
try:
    os.rename(destdir, origdir)
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

copy_dir(origdir, destdir)
migrate(destdir)


