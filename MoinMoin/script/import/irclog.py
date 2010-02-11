# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Push files into the wiki.

@copyright: 2005-2007 MoinMoin:AlexanderSchremmer
            2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

# this function generates a pagename from the file name
def filename_function(filename):
    filename = filename.lstrip('#')
    splitted = filename.split('.')
    return '/'.join(splitted[0:2])

class IAmRoot(object):
    def __getattr__(self, name):
        return lambda *args, **kwargs: True


import os

from MoinMoin.PageEditor import PageEditor
from MoinMoin.script import MoinScript

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
    """\
Purpose:
========
This script pushes files from a directory into the wiki (to be exact: it
pushes all except the last file, as this is maybe still written to in
case of irc logs).
One application is to use it to store IRC logs into the wiki.

Detailed Instructions:
======================
General syntax: moin [options] import irclog [irclog-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[irclog-options] see below:
    0. To add all the files in the current directory to the wiki as the user 'JohnSmith'
       moin ... import irclog --author=JohnSmirh --file-dir=.
"""

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
        self.parser.add_option("--acl", dest="acl", default="", help="Set a specific ACL for the pages.")

    def mainloop(self):
        self.init_request()
        request = self.request
        request.user.may = IAmRoot()
        request.cfg.mail_enabled = False
        for root, dirs, files in os.walk(self.options.file_dir):
            files.sort()
            for filename in files:
                pagename = self.options.page + filename_function(filename)
                #print "Pushing %r as %r" % (filename, pagename)
                p = PageEditor(request, pagename, do_editor_backup=0, uid_override=self.options.author, do_revision_backup=0)
                if p.exists():
                    if filename != files[-1]:
                        continue
                else:
                    p = PageEditor(request, pagename, do_editor_backup=0, uid_override=self.options.author)

                fileObj = open(os.path.join(root, filename), 'rb')
                try:
                    acl = ""
                    if self.options.acl:
                        acl = "#acl %s\n" % (self.options.acl, )
                    p.saveText(acl + "#format irc\n" + decodeLinewise(fileObj.read()), 0)
                except PageEditor.Unchanged, e:
                    pass
                except PageEditor.SaveError, e:
                    print "Got %r" % (e, )
                fileObj.close()
        #print "Finished."

