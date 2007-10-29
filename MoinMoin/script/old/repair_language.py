#!/usr/bin/env python
""" repair-language - repair page language setting.

Usage:

    repair-language option

Options:

    verify - verify pages, does not change anything, print page revision
        that should be repaired.

    repair - repair all page revisions.

Step by step instructions:

 1. Stop your wiki.

 2. Make a backup of 'data' directory.

 3. Run this script from your wiki data directory, where your pages
    directory lives.

 4. Fix permissions on the data directory, as explained in HelpOnInstalling.

 5. Verify that pages are fine after repair, if you find a problem,
    restore your data directory from backup.

Why run this script?

    In patch-325 a new #language processing instruction has been added.
    Pages that specify the language with it are displayed using correct
    direction, even if language_default use different direction.

    In the past, pages used to have ##language:xx comment. This comment
    has no effect, and should be replaced with newer #language xx
    processing instruction.

    This script replace ##language:xx to #language xx  in page headers.
    It convert all page revisions, so you can safely revert back to old
    revision and get correct page direction.

    You can run the script multiple times if needed.

@copyright: 2004 Nir Soffer <nirs AT freeshell DOT org>
@license: GPL, see COPYING for details
"""

import codecs
import os, sys

# Insert THIS moin dir first into sys path, or you would run another
# version of moin!
sys.path.insert(0, '../..')

from MoinMoin import i18n
valid_languages = i18n.wikiLanguages()


def listdir(path):
    """ Return list of files in path, filtering certain files """
    names = [name for name in os.listdir(path)
             if not name.startswith('.') and
             not name.endswith('.pickle') and
             name != 'CVS']
    return names


def repairText(text):
    """ Repair page text

    We change only this type of lines that currently are in moinmaster
    ##language:\s*xx

    Warning: will not repair the language if there is more text on the
    same line, e.g. ##language:fr make it french!

    @param text: the page text, unicode
    @rtype: 2 tuple, (unicode, int)
    @return: text after replacement, lines changed
    """
    lineend = u'\r\n'
    needle = u'##language:'
    changed = 0

    # Get text lines
    lines = text.splitlines()

    # Look in page header
    for i in range(len(lines)):
        line = lines[i]
        if not line.startswith(u'#'):
            break # end of header

        if line.startswith(needle):
            # Get language from rest of line
            lang = line[len(needle):].strip()

            # Validate lang, make new style language processing
            # instruction.
            if lang in valid_languages:
                line = u'#language %s' % lang
                lines[i] = line
                changed += 1

    if changed:
        # Join lines back, make sure there is trailing line end
        text = lineend.join(lines) + lineend
    return text, changed


def processPages(path, repair):
    """ Process page directory

    @param repair: repair or just test
    """
    charset = 'utf-8'

    pages = [p for p in listdir(path) if os.path.isdir(os.path.join(path, p))]
    for page in pages:
        revdir = os.path.join(path, page, 'revisions')
        if not os.path.isdir(revdir):
            print 'Error: %s: missing revisions directory' % page
            continue

        for rev in listdir(revdir):
            revpath = os.path.join(revdir, rev)
            # Open file, read text
            f = codecs.open(revpath, 'rb', charset)
            text = f.read()
            f.close()
            text, changed = repairText(text)

            if changed and repair:
                # Save converted text
                f = codecs.open(revpath, 'wb', charset)
                f.write(text)
                f.close()
                print 'Repaired %s revision %s' % (page, rev)
            elif changed:
                print 'Should repair %s revision %s' % (page, rev)


if __name__ == '__main__':

    # Check for pages directory in current directory
    path = os.path.abspath('pages')
    if not os.path.isdir(path):
        print "Error: could not find 'pages' directory"
        print 'Run this script from your wiki data directory'
        print __doc__
        sys.exit(1)

    options = {'verify': 0, 'repair': 1, }

    if len(sys.argv) != 2 or sys.argv[1] not in options:
        print __doc__
        sys.exit(1)

    processPages(path, repair=options[sys.argv[1]])




