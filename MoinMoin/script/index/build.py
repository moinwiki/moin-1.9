# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - build xapian search engine's index

    You must run this script as owner of the wiki files, usually this is the
    web server user.

    @copyright: 2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript

class IndexScript(MoinScript):
    """ Xapian general index script class """

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

