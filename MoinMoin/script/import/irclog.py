# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Push files into the wiki.

    This script pushes files from a directory into the wiki (to be exact: it
    pushes all except the last file, as this is maybe still written to in
    case of irc logs).
    One application is to use it to store IRC logs into the wiki.

    Usage:
    moin --config-dir=... --wiki-url=... import irclog --author=IrcLogImporter --file-dir=.
    
    @copyright: 2005 by MoinMoin:AlexanderSchremmer
                2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

# this function generates a pagename from the file name
def filename_function(filename):
    filename = filename.lstrip('#')
    splitted = filename.split('.')
    return '/'.join(splitted[0:2])

import os

from MoinMoin.PageEditor import PageEditor
from MoinMoin.script._util import MoinScript

def decodeLinewise(text):
    resultList = []
    for line in text.splitlines():
        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded_line = line.decode("iso-8859-1")
        resultList.append(decoded_line)
    return '\n'.join(resultList)


class PluginScript(MoinScript):
    """ irclog importer script class """

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--author", dest="author", default="IrcLogImporter",
            help="Use AUTHOR for edit history / RecentChanges"
        )
        self.parser.add_option(
            "--file-dir", dest="file_dir", default='.',
            help="read files from DIRECTORY"
        )
    
    def mainloop(self):
        self.init_request()
        request = self.request
        for root, dirs, files in os.walk(self.options.file_dir):
            files.sort()
            for filename in files[:-1]: # do not push the last file as it is constantly written to
                pagename = self.options.page + filename_function(filename)
                print "Pushing %r as %r" % (filename, pagename)
                p = PageEditor(request, pagename, do_editor_backup=0, uid_override=self.options.author)
                if p.exists():
                    continue
                fileObj = open(os.path.join(root, filename), 'rb')
                try:
                    p.saveText("#format plain\n" + decodeLinewise(fileObj.read()), 0)
                except PageEditor.SaveError, e:
                    print "Got %r" % (e, )
                fileObj.close()
        print "Finished."

