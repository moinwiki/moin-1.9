#!/usr/bin/env python
"""
    migration from moin 1.3 < patch-101 to moin 1.3 >= patch-101
    We heavily change the file system layout here:
    * data/backup/PageName.<UTC timestamp> -> data/pages/PageName/backup/<UTC timestamp>
    * data/text/PageName -> data/pages/PageName/text
    * data/pages/PageName/edit-lock stays the same
    * data/pages/PageName/last-edited isn't used any more as we have the same in last line of page edit-log
    * data/pages/PageName/attachments/* stays the same
    * data/editlog -> stays there (as edit-log), but also gets splitted into data/pages/PageName/edit-log
    * data/event.log -> stays there (as event-log)

    We will use this, but don't need to convert, as it will be recreated automatically:
    * data/cache/Page.py/PageName.<formatter> -> data/pages/PageName/cache/<formatter>
    * data/cache/pagelinks/PageName -> data/pages/PageName/cache/pagelinks
    * data/cache/charts/hitcounts-PageName -> data/pages/PageName/cache/hitcounts


    Steps for a successful migration:

        1. Stop your wiki and make a backup of old data and code

        2. Make a copy of the wiki's "data" directory to your working dir

        3. Run this script from your working dir

        4. If there was no error, you will find:
            data.pre-mig3 - the script renames your data directory copy to that name
            data - converted data dir

        5. Verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed.

        6. Copy additional files from data.pre-mig3 to data (maybe intermaps, logs,
           etc.). Be aware that the file contents AND file names of wiki content
           may have changed, so DO NOT copy the files inside the cache/ directory,
           let the wiki refill it.

        7. Replace the data directory your wiki uses with the data directory
           you created by previous steps. DO NOT simply copy the converted stuff
           into the original or you will duplicate pages and create chaos!

        8. Test it - if something has gone wrong, you still have your backup.


    @copyright: 2004 Thomas Waldmann
    @license: GPL, see COPYING for details
"""

import os, sys, shutil, urllib

sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, copy_file, copy_dir, listdir

origdir = 'data.pre-mig3'

def convert_textdir(dir_from, dir_to, is_backupdir=0):
    for fname_from in listdir(dir_from):
        if is_backupdir:
            fname, timestamp = fname_from.split('.')
        else:
            fname = fname_from
        try:
            os.mkdir(opj(dir_to, 'pages', fname))
        except: pass
        try:
            os.mkdir(opj(dir_to, 'pages', fname, 'backup'))
        except: pass
        try:
            os.mkdir(opj(dir_to, 'pages', fname, 'cache'))
        except: pass
        if is_backupdir:
            fname_to = opj('pages', fname, 'backup', timestamp)
        else:
            fname_to = opj('pages', fname, 'text')
        copy_file(opj(dir_from, fname_from), opj(dir_to, fname_to))

        #we don't have cache, mig2 doesn't convert it
        #try:
        #    cache_from = opj(origdir,'cache','charts','hitcounts-%s' % fname)
        #    cache_to = opj(dir_to, 'pages', fname, 'cache', 'hitcounts')
        #    if os.path.exists(cache_from):
        #        copy_file(cache_from, cache_to)
        #except: pass


def convert_pagedir(dir_from, dir_to):
    os.mkdir(dir_to)
    for dname_from in listdir(dir_from):
        print "%s" % (dname_from, )
        dname_to = dname_from
        shutil.copytree(opj(dir_from, dname_from), opj(dir_to, dname_to), 1)
        try:
            os.remove(opj(dir_to, dname_to, 'last-edited'))
        except: pass


def convert_editlog(file_from, file_to, dir_to):
    for l in open(file_from):
        data = l.split('\t')
        pagename = data[0]
        timestamp = data[2]
        data[2] = str(long(float(timestamp))) # we only want integer (must be long for py 2.2.x)
        data = '\t'.join(data)

        f = open(file_to, 'a')
        f.write(data)
        f.close()

        try:
            file_to2 = opj(dir_to, pagename, 'edit-log')
            f = open(file_to2, 'a')
            f.write(data)
            f.close()
        except: pass

# Backup original dir and create new empty dir
try:
    os.rename('data', origdir)
    os.mkdir('data')
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

convert_pagedir(opj(origdir, 'pages'), opj('data', 'pages'))

convert_textdir(opj(origdir, 'text'), 'data')

convert_textdir(opj(origdir, 'backup'), 'data', 1)

convert_editlog(opj(origdir, 'editlog'),
                opj('data', 'edit-log'),
                opj('data', 'pages'))

copy_file(opj(origdir, 'event.log'), opj('data', 'event.log'))

copy_dir(opj(origdir, 'plugin'), opj('data', 'plugin'))

copy_dir(opj(origdir, 'user'), opj('data', 'user'))

copy_file(opj(origdir, 'intermap.txt'), opj('data', 'intermap.txt'))

