#!/usr/bin/env python
"""
Migration from moin--main--1.3 pre patch-332 to post patch-332.

In patch-332 we changed the format of page lists in user data file. They
are now tab separated instead of comma separated, and page names are not
quoted using file system quoting.

You can run the script multiple times with no damage.


Steps for a successful migration:

 1. Stop your wiki

 2. Make a backup of your wiki 'data' directory

    WARNING: THIS SCRIPT MIGHT CORRUPT YOUR 'DATA' DIRECTORY. DON'T
    COMPLAIN LATER, MAKE BACKUP NOW!

 3. Move the wiki's 'data' directory to your working dir

 4. Run this script from your working dir

 5. If there was no error, you will find:
    data.pre-mig9   - backup of original data directory
    data            - converted data dir

 6. Verify conversion results (number of pages, size of logs,
    attachments, number of backup copies) - everything should be
    reasonable before you proceed.

    NOTE: THE CACHE DIRECTORY IS NOT COPIED - DO NOT COPY IT, IT WILL BE
    CREATED AND FILLED BY THE WIKI AUTOMATICALLY.

 7. Move the converted data directory into your wiki. Do not simply copy
    the converted stuff into the original or you will duplicate pages
    and create chaos!

 8. Fix permissions on your data directory, see HelpOnInstalling.

 9. Test it - if something has gone wrong, you still have your backup.


@copyright: 2004 Thomas Waldmann
@license: GPL, see COPYING for details
"""

import os, sys, codecs
join = os.path.join

# Insert THIS moin dir first into sys path, or you might run another
# version of moin and get unpredicted results!
sys.path.insert(0, '../../../..')

from MoinMoin import wikiutil, user
from MoinMoin.script.migration import migutil


def convert_quicklinks(string):
    """ Convert quicklinks from pre patch-332 to new format """
    # No need to convert new style list
    if '\t' in string:
        return string

    names = [name.strip() for name in string.split(',')]
    names = [wikiutil.unquoteWikiname(name) for name in names if name != '']
    string = user.encodeList(names)
    return string


def convert_subscribed_pages(string):
    """ Convert subscribed pages from pre patch-332 to new format """
    # No need to convert new style list
    if '\t' in string:
        return string

    # This might break pages that contain ',' in the name, we can't do
    # anything about it. This was the reason we changed the format.
    names = [name.strip() for name in string.split(',')]
    string = user.encodeList(names)
    return string


def convertUserData(text):
    """ Convert user data

    @param text: text of user file, unicode
    @rtype: unicode
    @return: convected user data
    """
    lines = text.splitlines()
    for i in range(len(lines)):
        line = lines[i]
        try:
            key, value = line.split('=', 1)
        except ValueError:
            continue
        if key == u'quicklinks':
            value = convert_quicklinks(value)
        elif key == u'subscribed_pages':
            value = convert_subscribed_pages(value)
        lines[i] = u'%s=%s' % (key, value)

    # Join back, append newline to last line
    text = u'\n'.join(lines) + u'\n'
    return text


def convertUsers(srcdir, dstdir):
    """ Convert users files

    @param srcdir: old users dir
    @param dstdir: new users dir
    """
    charset = 'utf-8'

    # Create dstdir
    if not os.path.exists(dstdir):
        try:
            os.mkdir(dstdir)
        except OSError:
            migutil.fatalError("can't create user directory at '%s'" % dstdir)

    if not os.path.isdir(srcdir):
        migutil.fatalError("can't find user directory at '%s'" % srcdir)

    for name in migutil.listdir(srcdir):
        if name == 'README' or name.endswith('.trail'):
            # Copy as is
            migutil.copy_file(join(srcdir, name), join(dstdir, name))
        else:
            srcfile = join(srcdir, name)
            f = codecs.open(srcfile, 'rb', charset)
            text = f.read()
            f.close()
            text = convertUserData(text)
            dstfile = join(dstdir, name)
            f = codecs.open(dstfile, 'wb', charset)
            f.write(text)
            f.close()
            print "Converted '%s' to '%s'" % (srcfile, dstfile)


if __name__ == '__main__':

    # Backup original dir
    datadir = 'data'
    origdir = 'data.pre-mig9'
    migutil.backup(datadir, origdir)

    # Copy ALL stuff from original dir into new data dir. Don't change
    # or drop anything from the original directory expect cache files.
    names = ['edit-log', 'event-log', 'intermap.txt', 'pages', 'plugin']
    migutil.copy(names, origdir, datadir)

    # Convert user directory
    convertUsers(join(origdir, 'user'), join(datadir, 'user'))

