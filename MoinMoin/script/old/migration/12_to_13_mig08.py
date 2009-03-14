#!/usr/bin/env python
"""
    migration from moin 1.3 < patch-305 to moin 1.3 >= patch-305
    Here we fix 2 errors that crept in by use of mig1(?) and mig5:
    * the edit-log misses 1 field (missing TAB) on faked "missing editlog
      entry" entries
    * we accidently gave ATTNEW/DRW/DEL an incremented revno (although
      attaching a file doesn't change page content and revision), so we need
      to convert those entries to use revno == 99999999 and renumber the
      normal entries so we have no missing numbers in between
    * edit-log's action field sometimes was empty (default: SAVE)

    Steps for a successful migration:

        1. Stop your wiki and make a backup of old data and code

        2. Make a copy of the wiki's "data" directory to your working dir

        3. Run this script from your working dir

        4. If there was no error, you will find:
            data.pre-mig8 - the script renames your data directory copy to that name
            data - converted data dir

        5. Verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed.

        6. Copy additional files from data.pre-mig8 to data (maybe intermaps, logs,
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

# info[pagename][timestamp_usecs] = [revno_new, [...]]
# if revno_new is 99999999, we haven't assigned a new revno to this entry
info = {}

def gather_editlog(el_from, forcepagename=None):
    """ this gathers everything that is in edit-log into internal
        data structures, converting to the future format
    """
    if not os.path.exists(el_from):
        return
    for l in open(el_from):
        data = l.rstrip('\n').rstrip('\r').split('\t')
        while len(data) < 9:
            data.append('')
        (timestampstr, revstr, action, pagename, ip, host, id, extra, comment) = data

        if forcepagename: # we use this for edit-log in pagedirs (for renamed pages!)
            pagename = forcepagename

        if not action: # FIX: sometimes action is empty ...
            action = 'SAVE'

        if action in ['ATTNEW', 'ATTDRW', 'ATTDEL', ]:
            revstr = '99999999' # FIXES revno
            # use reserved value, ATT action doesn't create new rev of anything

        if (comment == '' and extra == '' and id == 'missing editlog entry for this page version') or \
           (extra == '' and id == '' and comment == 'missing editlog entry for this page version'):
            # FIX omitted field bug on fake entries
            comment = 'missing edit-log entry for this revision' # more precise
            extra = ''
            id = ''

        rev = int(revstr)
        data = [timestampstr, rev, action, pagename, ip, host, id, extra, comment]

        entry = info.get(pagename, {})
        timestamp = long(timestampstr) # must be long for py 2.2.x
        entry[timestamp] = [99999999, data] # new revno, data
        info[pagename] = entry

def gather_pagedirs(dir_from):
    """ this gathers edit-log information from the pagedirs, just to make sure
    """
    pagedir = opj(dir_from, 'pages')
    pagelist = listdir(pagedir)
    for pagename in pagelist:
        editlog_from = opj(pagedir, pagename, 'edit-log')
        gather_editlog(editlog_from, pagename)


def generate_pages(dir_from, dir_to):
    revactions = ['SAVE', 'SAVENEW', 'SAVE/REVERT', ] # these actions create revisions
    for pn in info:
        entry = info.get(pn, {})
        tslist = entry.keys()
        if tslist:
            pagedir = opj(dir_to, 'pages', pn)
            revdir = opj(pagedir, 'revisions')
            os.makedirs(revdir)
            editlog_file = opj(pagedir, 'edit-log')
            f = open(editlog_file, 'w')
            revnew = 0
            tslist.sort()
            for ts in tslist:
                data = entry[ts][1]
                datanew = data[:]
                (timestamp, rev, action, pagename, ip, host, id, extra, comment) = data
                revstr = '%08d' % rev
                if action in revactions:
                    revnew += 1
                    revnewstr = '%08d' % revnew
                    entry[ts][0] = revnew # remember what new revno we chose
                else: # ATTNEW,ATTDRW,ATTDEL
                    revnewstr = '99999999'
                if action.endswith('/REVERT'):
                    # replace the old revno with the correct new revno
                    revertrevold = int(extra)
                    revertrevnew = 0
                    for ts2 in tslist:
                        data2 = entry[ts2][1]
                        (timestamp2, rev2, action2, pagename2, ip2, host2, id2, extra2, comment2) = data2
                        if rev2 == revertrevold:
                            revertrevnew = entry[ts2][0]
                    datanew[7] = '%08d' % revertrevnew

                datanew[1] = revnewstr
                f.write('\t'.join(datanew)+'\n') # does make a CRLF on win32 in the file

                if action in revactions: # we DO have a page rev for this one
                    file_from = opj(dir_from, 'pages', pn, 'revisions', revstr)
                    file_to = opj(revdir, revnewstr)
                    copy_file(file_from, file_to)
            f.close()

            # check if page exists or is deleted in orig dir
            pagedir_from = opj(dir_from, 'pages', pn)
            revdir_from = opj(pagedir_from, 'revisions')
            try:
                curr_file_from = opj(pagedir_from, 'current')
                currentfrom = open(curr_file_from).read().strip() # try to access it
                page_exists = 1
            except:
                page_exists = 0

            # re-make correct DELETED status!
            if page_exists:
                curr_file = opj(pagedir, 'current')
                f = open(curr_file, 'w')
                f.write("%08d\n" % revnew) # we add a \n, so it is easier to hack in there manually
                f.close()

        att_from = opj(dir_from, 'pages', pn, 'attachments')
        if os.path.exists(att_from):
            att_to = opj(pagedir, 'attachments')
            copy_dir(att_from, att_to)


def generate_editlog(dir_from, dir_to):
    editlog = {}
    for pagename in info:
        entry = info.get(pagename, {})
        for ts in entry:
            file_from, data = entry[ts]
            editlog[ts] = data

    tslist = editlog.keys()
    tslist.sort()

    editlog_file = opj(dir_to, 'edit-log')
    f = open(editlog_file, 'w')
    for ts in tslist:
        datatmp = editlog[ts][:]
        rev = datatmp[1]
        datatmp[1] = '%08d' % rev
        f.write('\t'.join(datatmp)+'\n')
    f.close()


origdir = 'data.pre-mig8'

# Backup original dir and create new empty dir
try:
    os.rename('data', origdir)
    os.mkdir('data')
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

#gather_editlog(opj(origdir, 'edit-log'))
gather_pagedirs(origdir)

generate_editlog(origdir, 'data')
generate_pages(origdir, 'data')

copy_dir(opj(origdir, 'plugin'), opj('data', 'plugin'))

copy_dir(opj(origdir, 'user'), opj('data', 'user'))

copy_file(opj(origdir, 'event-log'), opj('data', 'event-log'))

copy_file(opj(origdir, 'intermap.txt'), opj('data', 'intermap.txt'))


