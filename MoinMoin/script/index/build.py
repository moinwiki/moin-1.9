# -*- coding: iso-8859-1 -*-
"""
MoinMoin - build xapian search engine's index

@copyright: 2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript

class IndexScript(MoinScript):
    """\
Purpose:
========
This tool allows you to control xapian's index of Moin.

Detailed Instructions:
======================
General syntax: moin [options] index build [build-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[build-options] see below:
    0. You must run this script as owner of the wiki files, usually this is the
       web server user.

    1. To add the files from '/files.lst' to the index
       moin ... index build --files /files.lst --mode add

    2. To update the index with the files from '/files.lst'
       moin ... index build --files /files.lst --mode update

    3. To rebuild the index with the files from '/files.lst'
       moin ... index build --files /files.lst --mode rebuild
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--files", metavar="FILES", dest="file_list",
            help="filename of file list, e.g. files.lst (one file per line)"
        )
        self.parser.add_option(
            "--mode", metavar="MODE", dest="mode",
            help="either add (unconditionally add to index), update (update an existing index) or rebuild (remove and add)"
        )

    def mainloop(self):
        self.init_request()
        # Do we have additional files to index?
        if self.options.file_list:
            self.files = file(self.options.file_list)
        else:
            self.files = None
        self.command()

class PluginScript(IndexScript):
    """ Xapian index build script class """

    def command(self):
        from MoinMoin.search.Xapian import Index
        Index(self.request).indexPages(self.files, self.options.mode)

