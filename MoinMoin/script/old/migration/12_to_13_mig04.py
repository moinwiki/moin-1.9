#!/usr/bin/env python
"""
    migration from moin 1.3 < patch-196 to moin 1.3 >= patch-196
    Because of trouble with float timestamps, we migrate to usec timestamp resolution here.
    * data/pages/PageName/backup/<UTC timestamp> -> .../<UTC timestamp in usecs>
    * data/user/<uid>.bookmark -> convert to usecs
    * data/edit-log and data/pages/PageName/edit-log -> convert to usecs
    * data/event-log -> convert to usecs

    Steps for a successful migration:

        1. Stop your wiki and make a backup of old data and code

        2. Make a copy of the wiki's "data" directory to your working dir

        3. Run this script from your working dir

        4. If there was no error, you will find:
            data.pre-mig4 - the script renames your data directory copy to that name
            data - converted data dir

        5. Verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed.

        6. Copy additional files from data.pre-mig4 to data (maybe intermaps, logs,
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


import os.path, sys, urllib

sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, copy_dir

def convert_ts(ts_from):
    if ts_from > 5000000000: # far more than 32bits?
        ts_to = ts_from # we already have usec kind of timestamp
    else:
        ts_to = wikiutil.timestamp2version(ts_from)
    return long(ts_to) # must be long for py 2.2.x

def convert_eventlog(file_from, file_to):
    if not os.path.exists(file_from):
        return
    f = open(file_to, 'a')
    for l in open(file_from):
        if not l.strip():
            continue
        data = l.split('\t')
        data[0] = str(convert_ts(float(data[0]))) # we want usecs
        data = '\t'.join(data)
        f.write(data)
    f.close()

def convert_editlog(file_from, file_to):
    if not os.path.exists(file_from):
        return
    f = open(file_to, 'a')
    for l in open(file_from):
        data = l.split('\t')
        pagename = data[0]
        timestamp = data[2]
        data[2] = str(convert_ts(float(timestamp))) # we want usecs
        data = '\t'.join(data)
        f.write(data)
    f.close()

def convert_pagedir(dir_from, dir_to, is_backupdir=0):
    os.mkdir(dir_to)
    for pagedir in listdir(dir_from):
        text_from = opj(dir_from, pagedir, 'text')
        text_to = opj(dir_to, pagedir, 'text')
        os.mkdir(opj(dir_to, pagedir))
        copy_file(text_from, text_to)

        backupdir_from = opj(dir_from, pagedir, 'backup')
        backupdir_to = opj(dir_to, pagedir, 'backup')
        if os.path.exists(backupdir_from):
            os.mkdir(backupdir_to)
            for ts in listdir(backupdir_from):
                ts_usec = str(convert_ts(float(ts)))
                backup_from = opj(backupdir_from, ts)
                backup_to = opj(backupdir_to, ts_usec)
                copy_file(backup_from, backup_to)

        editlog_from = opj(dir_from, pagedir, 'edit-log')
        editlog_to = opj(dir_to, pagedir, 'edit-log')
        convert_editlog(editlog_from, editlog_to)

        #cachedir_from = opj(dir_from, pagedir, 'cache')
        #cachedir_to = opj(dir_to, pagedir, 'cache')
        #if os.path.exists(cachedir_from):
        #    os.mkdir(cachedir_to)
        #    try:
        #        copy_file(
        #            opj(cachedir_from, 'hitcounts'),
        #            opj(cachedir_to, 'hitcounts'))
        #    except: pass

        attachdir_from = opj(dir_from, pagedir, 'attachments')
        attachdir_to = opj(dir_to, pagedir, 'attachments')
        if os.path.exists(attachdir_from):
            try:
                copy_dir(attachdir_from, attachdir_to)
            except: pass


def convert_userdir(dir_from, dir_to):
    os.mkdir(dir_to)
    for fname in listdir(dir_from):
        if fname.endswith('.bookmark'):
            bm = open(opj(dir_from, fname)).read().strip()
            bm = str(wikiutil.timestamp2version(float(bm)))
            f = open(opj(dir_to, fname), 'w')
            f.write(bm)
            f.close()
        else:
            copy_file(opj(dir_from, fname), opj(dir_to, fname))


origdir = 'data.pre-mig4'

# Backup original dir and create new empty dir
try:
    os.rename('data', origdir)
    os.mkdir('data')
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

convert_pagedir(opj(origdir, 'pages'), opj('data', 'pages'))

convert_editlog(opj(origdir, 'edit-log'), opj('data', 'edit-log'))

convert_eventlog(opj(origdir, 'event.log'), opj('data', 'event-log'))

convert_userdir(opj(origdir, 'user'), opj('data', 'user'))

copy_dir(opj(origdir, 'plugin'), opj('data', 'plugin'))

copy_file(opj(origdir, 'intermap.txt'), opj('data', 'intermap.txt'))

