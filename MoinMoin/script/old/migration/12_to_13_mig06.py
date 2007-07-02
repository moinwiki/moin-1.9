#!/usr/bin/env python
"""
    12_to_13.py - migration from < moin--main--patch-248 to >= patch 249
    * convert event-log from iso8859-1 to config.charset (utf-8) encoding

    Steps for a successful migration to utf-8:
        1. stop your wiki and make a backup
        2. make a copy of the wiki's "data" directory to your working dir
        3. clean up your working copy of the data dir:
            a. if you use CVS or GNU arch remove stuff like CVS/, .cvsignore
               or .arch-ids/ etc.
            b. remove *.pickle (used by moin for caching some information,
               will be re-created automatically), especially:
                   I. data/user/userdict.pickle
                   II. data/dicts.pickle
            c. if you used symlinks in data/text or elsewhere, remove them
        4. make sure that from_encoding and to_encoding matches your needs (see
           beginning of script below and config.charset in moin_config.py) and
           run python2.3 12_to_13_mig6.py from your working dir
        5. if there was no error, you will find:
            data.pre-mig6 (the script renames your data directory copy to that name)
            data (result, converted to utf-8)
        6. verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed. Usually the file size gets larger when converting from
           iso8859-1 (or other non-unicode charset) to utf-8 except if your
           content is ASCII-only, then it will keep its size.
        7. copy additional files from data.pre-mig6 to data (maybe intermaps, logs,
           etc.). Be aware that the file contents AND file names of wiki content
           may have changed, so DO NOT copy the cache/ directory, but let
           the wiki recreate it.
        8. replace the data directory your wiki uses with the data directory
           you created by previous steps. DO NOT simply copy the converted stuff
           into the original or you will duplicate pages and create chaos!
        9. test it. if something has gone wrong, you still have your backup.


        10. if you use dictionaries for spellchecking, you have to convert them
            to config.charset, too. Remove your dict.cache before re-starting
            your wiki.

    @copyright: 2004 Thomas Waldmann
    @license: GPL, see COPYING for details
"""

from_encoding = 'iso8859-1'
to_encoding = 'utf-8'

import os.path, sys, shutil, urllib

sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, copy_dir

def convert_string(str, enc_from, enc_to):
    return str.decode(enc_from).encode(enc_to)

def convert_eventlog(fname_from, fname_to, enc_from, enc_to):
    print "%s -> %s" % (fname_from, fname_to)
    file_from = open(fname_from)
    file_to = open(fname_to, "w")

    for line in file_from:
        line = line.replace('\r', '')
        line = line.replace('\n', '')
        fields = line.split('\t')
        kvpairs = fields[2]
        kvpairs = kvpairs.split('&')
        kvlist = []
        for kvpair in kvpairs:
            key, val = kvpair.split('=')
            key = urllib.unquote(key)
            val = urllib.unquote(val)
            key = convert_string(key, enc_from, enc_to)
            val = convert_string(val, enc_from, enc_to)
            key = urllib.quote(key)
            val = urllib.quote(val)
            kvlist.append("%s=%s" % (key, val))
        fields[2] = '&'.join(kvlist)
        line = '\t'.join(fields) + '\n'
        file_to.write(line)

    file_to.close()
    file_from.close()
    st = os.stat(fname_from)
    os.utime(fname_to, (st.st_atime, st.st_mtime))

origdir = 'data.pre-mig6'

try:
    os.rename('data', origdir)
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

copy_dir(origdir, 'data')
os.remove(opj('data', 'event-log')) # old format
convert_eventlog(opj(origdir, 'event-log'), opj('data', 'event-log'), from_encoding, to_encoding)


