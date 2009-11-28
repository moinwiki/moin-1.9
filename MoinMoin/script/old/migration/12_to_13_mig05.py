#!/usr/bin/env python
"""
    migration from moin 1.3 < patch-221 to moin 1.3 >= patch-221
    We need to make versioning completely different. Problem:
        * old versioning used UNIX timestamps (32bits), but had collisions due
          to seconds resolution (on the FS, they were avoided by using floats
          in early moin versions, but floats suck and xmlrpc only does ints).
        * then we moved to usecs resolution, collision problem solved, but
          xmlrpc broke because it can't handle long ints. Oh well ... 8-(
        * So for the 3rd try, we now just enumerate versions 1,2,3,4,...
          This makes xmlrpc happy again (and matches better how xmlrpc was
          designed, as it has separate fields for timestamp and version),
          but we now have to keep the timestamp somewhere else. The appropriate
          place is of course the edit-log.

    So we change like this:
        * data/pages/PageName/backup/<UTC timestamp in usecs>
          -> data/pages/PageName/revisions/<revno>
    A page save is now done like that:
        * mv 'current' 'notcurrent'
        * if success ('current' was there):
            * revno = read('notcurrent')
            * revno++
            * write('notcurrent', revno)
            * save to revisions/<revno>
            * mv 'notcurrent' 'current'
        * else give error msg and let user retry save

    * data/user/<uid>.bookmark stays in usecs
    * data/event-log stays in usecs
    * data/edit-log and data/pages/PageName/edit-log stay in usecs and:
        * old: PageName UserIp TimeUSecs UserHost UserId Comment Action
        * new: TimeUSecs PageRev Action PageName UserIp UserHost UserId Extra Comment
        *                =======                                        =====
         * PageRev is identical to the filename in revisions/ directory
         * Extra is used for some stuff formerly put into comment field, like
           revert info or attach filename

    Steps for a successful migration:

        1. Stop your wiki and make a backup of old data and code

        2. Make a copy of the wiki's "data" directory to your working dir

        3. Run this script from your working dir

        4. If there was no error, you will find:
            data.pre-mig5 - the script renames your data directory copy to that name
            data - converted data dir

        5. Verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed.

        6. Copy additional files from data.pre-mig5 to data (maybe intermaps, logs,
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

# Insert THIS moin dir first into sys path, or you would run another
# version of moin!
sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, move_file, copy_dir

# info[pagename][timestamp_usecs] = (file_from, (...))
# if file_from is None, we have just a log entry, but no associated file yet
info = {}
info2 = {}
exists = {}
pagelist = []

def gather_editlog(dir_from, el_from):
    """ this gathers everything that is in edit-log into internal
        data structures, converting to the future format
    """
    if not os.path.exists(el_from):
        return
    for l in open(el_from):
        data = l.rstrip('\n').split('\t')
        origlen = len(data)
        while len(data) < 7: data.append('')
        (pagename, ip, timestamp, host, id, comment, action) = data
        if origlen == 6:
            action = comment
            comment = ''

        extra = ''
        if action == 'SAVE/REVERT': # we missed to convert that in mig4
            ts = long(comment) # must be long for py 2.2.x
            if ts < 4000000000: # UNIX timestamp (secs)
                extra = str(wikiutil.timestamp2version(ts))
            else: # usecs timestamp
                extra = str(ts)
            # later we convert this timestamp to a revision number
            comment = ''
        if action in ['ATTNEW', 'ATTDRW', 'ATTDEL', ]:
            extra = comment # filename
            comment = '' # so we can use comments on ATT* in future

        timestamp = long(timestamp) # must be long for py 2.2.x
        data = [timestamp, '', action, pagename, ip, host, id, extra, comment]

        entry = info.get(pagename, {})
        entry[timestamp] = [None, data]
        info[pagename] = entry

def gather_pagedirs(dir_from, is_backupdir=0):
    """ this gathers information from the pagedirs, i.e. text and backup
        files (and also the local editlog) and tries to merge/synchronize
        with the informations gathered from editlog
    """
    global pagelist
    pagelist = listdir(dir_from)
    for pagename in pagelist:
        editlog_from = opj(dir_from, pagename, 'edit-log')
        gather_editlog(dir_from, editlog_from)

        entry = info.get(pagename, {})

        loglist = [] # editlog timestamps of page revisions
        for ts, data in entry.items():
            if data[1][2] in ['SAVE', 'SAVENEW', 'SAVE/REVERT', ]:
                loglist.append(ts)
        loglist.sort()
        lleftover = loglist[:]

        # remember the latest log entry
        if lleftover:
            llatest = lleftover[-1]
        else:
            llatest = None

        backupdir_from = opj(dir_from, pagename, 'backup')
        if os.path.exists(backupdir_from):
            backuplist = listdir(backupdir_from)
            bleftover = backuplist[:]
            for bfile in backuplist:
                backup_from = opj(backupdir_from, bfile)
                ts = long(bfile)
                if ts in loglist: # we have an editlog entry, exact match
                    entry[ts][0] = backup_from
                    lleftover.remove(ts)
                    bleftover.remove(bfile)

        text_from = opj(dir_from, pagename, 'text')
        found_text = False
        if os.path.exists(text_from): # we have a text file, it should match latest log entry
            exists[pagename] = True
            mtime = os.path.getmtime(text_from)
            if llatest and llatest in lleftover:
                ts = llatest
                if abs(wikiutil.timestamp2version(mtime) - ts) < 2000000: # less than a second diff
                    entry[ts][0] = text_from
                    lleftover.remove(ts)
                    found_text = True
            else: # we have no log entries left 8(
                ts = wikiutil.timestamp2version(mtime)
                data = [ts, '', 'SAVE', pagename, '', '', '', '', 'missing editlog entry for this page version']
                entry[ts] = [text_from, data]
        else:
            # this page was maybe deleted, so we remember for later:
            exists[pagename] = False
            if llatest in lleftover: # if a page is deleted, the last log entry has no file
                entry[llatest][0] = None
                lleftover.remove(llatest)

        if os.path.exists(backupdir_from):
            backuplist = listdir(backupdir_from)
            for bfile in backuplist:
                if not bfile in bleftover: continue
                backup_from = opj(backupdir_from, bfile)
                bts = long(bfile) # must be long for py 2.2.x
                for ts in lleftover:
                    tdiff = abs(bts-ts)
                    if tdiff < 2000000: # editlog, inexact match
                        entry[ts][0] = backup_from
                        lleftover.remove(ts)
                        bleftover.remove(bfile)
                    elif 3599000000 <= tdiff <= 3601000000: # editlog, win32 daylight saving bug
                        entry[ts][0] = backup_from
                        lleftover.remove(ts)
                        bleftover.remove(bfile)
                        print "Warning: Win32 daylight saving bug encountered & fixed!"

            if len(bleftover) == 1 and len(lleftover) == 1: # only 1 left, must be this
                backup_from = opj(backupdir_from, bleftover[0])
                entry[lleftover[0]][0] = backup_from
                lleftover = []
                bleftover = []

            # fake some log entries
            for bfile in bleftover:
                backup_from = opj(backupdir_from, bfile)
                bts = long(bfile) # must be long py 2.2.x
                data = [ts, '', 'SAVE', pagename, '', '', '', '', 'missing editlog entry for this page version']
                entry[bts] = [backup_from, data]

        # check if we still haven't matched the "text" file
        if not found_text and os.path.exists(text_from):
            if llatest in lleftover: # latest log entry still free
                entry[llatest][0] = text_from # take it. do not care about mtime of file.
                lleftover.remove(llatest)
            else: # log for "text" file is missing or latest was taken by other rev 8(
                mtime = os.path.getmtime(text_from)
                ts = wikiutil.timestamp2version(mtime) # take mtime, we have nothing better
                data = [ts, '', 'SAVE', pagename, '', '', '', '', 'missing editlog entry for this page version']
                entry[ts] = [text_from, data]

        # delete unmatching log entries
        for ts in lleftover:
            #print "XXX Deleting leftover log entry: %r" % entry[ts]
            del entry[ts]

        info[pagename] = entry

def remove_trash(dir_from):
    for pagename in info:
        # omit dead pages and MoinEditorBackup
        if pagename in pagelist and (
           os.path.exists(opj(dir_from, pagename, 'text')) or
           os.path.exists(opj(dir_from, pagename, 'backup'))
           ) and not pagename.endswith('MoinEditorBackup'):
            info2[pagename] = info[pagename]

def generate_pages(dir_from, dir_to):
    for pagename in info2:
        entry = info2.get(pagename, {})
        tslist = entry.keys()
        if tslist:
            pagedir = opj(dir_to, 'pages', pagename)
            os.makedirs(opj(pagedir, 'revisions'))
            editlog_file = opj(pagedir, 'edit-log')
            f = open(editlog_file, 'w')
            rev = 0
            tslist.sort()
            for ts in tslist:
                rev += 1
                revstr = '%08d' % rev
                file_from, data = entry[ts]
                data[0] = str(ts)
                data[1] = revstr
                if data[2].endswith('/REVERT'):
                    # replace the timestamp with the revision number
                    revertts = long(data[7]) # must be long for py 2.2.x
                    try:
                        revertrev = int(entry[revertts][1][1])
                    except KeyError:
                        # never should trigger...
                        print "********* KeyError %s entry[%d][1][1] **********" % (pagename, revertts)
                        revertrev = 0
                    data[7] = '%08d' % revertrev
                f.write('\t'.join(data)+'\n')
                if file_from is not None:
                    file_to = opj(pagedir, 'revisions', revstr)
                    copy_file(file_from, file_to)
            f.close()

            curr_file = opj(pagedir, 'current')
            f = open(curr_file, 'w')
            f.write(revstr)
            f.close()

        att_from = opj(dir_from, 'pages', pagename, 'attachments')
        if os.path.exists(att_from):
            att_to = opj(pagedir, 'attachments')
            copy_dir(att_from, att_to)


def generate_editlog(dir_from, dir_to):
    editlog = {}
    for pagename in info2:
        entry = info2.get(pagename, {})
        for ts in entry:
            file_from, data = entry[ts]
            editlog[ts] = data

    tslist = editlog.keys()
    tslist.sort()

    editlog_file = opj(dir_to, 'edit-log')
    f = open(editlog_file, 'w')
    for ts in tslist:
        data = editlog[ts]
        f.write('\t'.join(data)+'\n')
    f.close()


origdir = 'data.pre-mig5'

# Backup original dir and create new empty dir
try:
    os.rename('data', origdir)
    os.mkdir('data')
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

gather_editlog(origdir, opj(origdir, 'edit-log'))
gather_pagedirs(opj(origdir, 'pages'))

remove_trash(opj(origdir, 'pages'))

generate_pages(origdir, 'data')
generate_editlog(origdir, 'data')


copy_dir(opj(origdir, 'plugin'), opj('data', 'plugin'))

copy_dir(opj(origdir, 'user'), opj('data', 'user'))

copy_file(opj(origdir, 'event-log'), opj('data', 'event-log'))

copy_file(opj(origdir, 'intermap.txt'), opj('data', 'intermap.txt'))


