#!/usr/bin/env python
"""
    migration from moin 1.3 < patch-78 to moin 1.3 >= patch-78
    * switch quoting mechanism from (xx)(xx) to (xxxx)
    * charset isn't changed, it was utf-8 before and will be utf-8 after

    Steps for a successful migration:
        1. stop your wiki and make a backup
        2. make a copy of the wiki's "data" directory to your working dir
        3. run this script from your working dir
        4. if there was no error, you will find:
            data.pre-mig2 (the script renames your data directory copy to that name)
            data (result, converted)
        5. verify conversion results (number of pages, size of logs, attachments,
           number of backup copies) - everything should be reasonable before
           you proceed.
        6. copy additional files from data.pre-mig2 to data (maybe intermaps, logs,
           etc.). Be aware that the file contents AND file names of wiki content
           may have changed, so DO NOT copy the cache/ directory, but let
           the wiki recreate it.
        7. replace the data directory your wiki uses with the data directory
           you created by previous steps. DO NOT simply copy the converted stuff
           into the original or you will duplicate pages and create chaos!
        8. test it. if something has gone wrong, you still have your backup.
        9. if you use dictionaries for spellchecking, you have to convert them
           to config.charset, too. Remove your dict.cache before re-starting
           your wiki.

    @copyright: 2004 Thomas Waldmann
    @license: GPL, see COPYING for details
"""

from_encoding = 'utf-8'
to_encoding = 'utf-8'

import os.path, sys, shutil, urllib

sys.path.insert(0, '../../../..')
from MoinMoin import wikiutil

from MoinMoin.script.migration.migutil import opj, listdir, copy_file, copy_dir

# this is a copy of the wikiutil.unquoteWikiname of moin--main--1.3--patch-77
def unquoteWikinameOld(filename, charsets=[from_encoding, ]):
    """
    Return decoded original filename when given an encoded filename.
    @param filename: encoded filename
    @rtype: string
    @return: decoded, original filename
    """
    if isinstance(filename, type(u'')): # from some places we get called with unicode
        filename = filename.encode(from_encoding)
    fn = ''
    i = 0
    while i < len(filename):
        c = filename[i]
        if c == '(':
            c1 = filename[i+1]
            c2 = filename[i+2]
            close = filename[i+3]
            if close != ')':
                raise Exception('filename encoding invalid')
            i += 4
            fn = fn + chr(16 * int(c1, 16) + int(c2, 16))
        else:
            fn = fn + c
            i += 1
    return wikiutil.decodeUserInput(fn, charsets)


def convert_string(str, enc_from, enc_to):
    return str.decode(enc_from).encode(enc_to)


def qf_convert_string(str, enc_from, enc_to):
    """ Convert filename from pre patch 78 quoting to new quoting

    The old quoting function from patch 77 can convert name ONLY from
    the old way to the new, so if you have a partially converted
    directory, as it the situation as of moin--main--1.3--patch-86,
    it does not work.

    The new unquoting function is backward compatible, and can unquote
    both post and pre patch 78 file names.
    """
    str = wikiutil.unquoteWikiname(str, [enc_from])
    str = wikiutil.quoteWikinameFS(str, enc_to)
    return str


def convert_file(fname_from, fname_to, enc_from, enc_to):
    print "%s -> %s" % (fname_from, fname_to)
    file_from = open(fname_from)
    file_to = open(fname_to, "w")
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
            fname, timestamp = fname_from.split('.')
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
            fields = line.split('\t')
            fields[0] = qf_convert_string(fields[0], enc_from, enc_to)
            fields[5] = convert_string(fields[5], enc_from, enc_to)
            line = '\t'.join(fields)
            file_to.write(line)

origdir = 'data.pre-mig2'

# Backup original dir and create new empty dir
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

