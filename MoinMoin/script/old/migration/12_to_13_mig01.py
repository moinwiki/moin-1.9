#!/usr/bin/env python
"""
    12_to_13.py - migration from moin 1.2 to moin 1.3
    * switch the wiki to utf-8 encoding
    * switch quoting mechanism from _xx to (xx)
    * switch timestamps from float secs to int usecs

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
           run python 12_to_13_mig1.py from your working dir
        5. if there was no error, you will find:
            data.pre-mig1 (the script renames your data directory copy to that name)
            data (result, converted to utf-8)
        6. verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed. Usually the file size gets larger when converting from
           iso8859-1 (or other non-unicode charset) to utf-8 except if your
           content is ASCII-only, then it will keep its size.
        7. copy additional files from data.pre-mig1 to data (maybe intermaps, logs,
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
#from_encoding = 'utf-8'

to_encoding = 'utf-8'

import os.path, sys, shutil, urllib

sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, copy_dir

# this is a copy of the wikiutil.unquoteFilename of moin 1.2.1

def unquoteFilename12(filename, encoding):
    """
    Return decoded original filename when given an encoded filename.

    @param filename: encoded filename
    @rtype: string
    @return: decoded, original filename
    """
    str = urllib.unquote(filename.replace('_', '%'))
    try:
        newstr = str.decode(encoding)
    except UnicodeDecodeError: # try again with iso
        newstr = str.decode('iso-8859-1')
    return newstr

unquoteWikiname12 = unquoteFilename12


def convert_string(str, enc_from, enc_to):
    try:
        newstr = str.decode(enc_from)
    except UnicodeDecodeError: # try again with iso
        newstr = str.decode('iso-8859-1')
    return newstr.encode(enc_to)

def qf_convert_string(str, enc_from, enc_to):
    str = unquoteWikiname12(str, enc_from)
    str = wikiutil.quoteWikinameFS(str, enc_to)
    return str

def convert_file(fname_from, fname_to, enc_from, enc_to):
    print "%s -> %s" % (fname_from, fname_to)
    file_from = open(fname_from, "rb")
    if os.path.exists(fname_to):
        raise Exception("file exists %s" % fname_to)
    file_to = open(fname_to, "wb")
    for line in file_from:
        file_to.write(convert_string(line, enc_from, enc_to))
    file_to.close()
    file_from.close()
    st = os.stat(fname_from)
    os.utime(fname_to, (st.st_atime, st.st_mtime))

def convert_textdir(dir_from, dir_to, enc_from, enc_to, is_backupdir=0):
    os.mkdir(dir_to)
    for fname_from in listdir(dir_from):
        if is_backupdir:
            fname, timestamp = fname_from.split('.', 1)
            timestamp = str(wikiutil.timestamp2version(float(timestamp)))
        else:
            fname = fname_from
        fname = qf_convert_string(fname, enc_from, enc_to)
        if is_backupdir:
            fname_to = '.'.join([fname, timestamp])
        else:
            fname_to = fname
        convert_file(opj(dir_from, fname_from), opj(dir_to, fname_to),
                     enc_from, enc_to)

def convert_pagedir(dir_from, dir_to, enc_from, enc_to):
    os.mkdir(dir_to)
    for dname_from in listdir(dir_from):
        dname_to = qf_convert_string(dname_from, enc_from, enc_to)
        print "%s -> %s" % (dname_from, dname_to)
        shutil.copytree(opj(dir_from, dname_from), opj(dir_to, dname_to), 1)
        try:
            convert_editlog(opj(dir_from, dname_from, 'last-edited'),
                            opj(dir_to, dname_to, 'last-edited'),
                            enc_from, enc_to)
        except IOError:
            pass # we ignore if it doesnt exist

def convert_userdir(dir_from, dir_to, enc_from, enc_to):
    os.mkdir(dir_to)
    for fname in listdir(dir_from):
        convert_file(opj(dir_from, fname), opj(dir_to, fname),
                     enc_from, enc_to)

def convert_editlog(log_from, log_to, enc_from, enc_to):
        file_from = open(log_from)
        file_to = open(log_to, "w")
        for line in file_from:
            line = line.replace('\r', '')
            line = line.replace('\n', '')
            if not line.strip(): # skip empty lines
                continue
            fields = line.split('\t')
            fields[0] = qf_convert_string(fields[0], enc_from, enc_to)
            fields[2] = str(wikiutil.timestamp2version(float(fields[2])))
            if len(fields) < 6:
                fields.append('') # comment
            if len(fields) < 7:
                fields.append('SAVE') # action
            fields[5] = convert_string(fields[5], enc_from, enc_to)
            line = '\t'.join(fields) + '\n'
            file_to.write(line)

origdir = 'data.pre-mig1'

try:
    os.rename('data', origdir)
    os.mkdir('data')
except OSError:
    print "You need to be in the directory where your copy of the 'data' directory is located."
    sys.exit(1)

convert_textdir(opj(origdir, 'text'), opj('data', 'text'), from_encoding, to_encoding)

convert_textdir(opj(origdir, 'backup'), opj('data', 'backup'), from_encoding, to_encoding, 1)

convert_pagedir(opj(origdir, 'pages'), opj('data', 'pages'), from_encoding, to_encoding)

convert_userdir(opj(origdir, 'user'), opj('data', 'user'), from_encoding, to_encoding)

convert_editlog(opj(origdir, 'editlog'), opj('data', 'editlog'), from_encoding, to_encoding)

copy_file(opj(origdir, 'event.log'), opj('data', 'event.log'))

copy_dir(opj(origdir, 'plugin'), opj('data', 'plugin'))

copy_file(opj(origdir, 'intermap.txt'), opj('data', 'intermap.txt'))


