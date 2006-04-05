# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - build lupy search engine's index

    You must run this script as owner of the wiki files, usually this is the
    web server user.

    @copyright: 2005 by Florian Festi, Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

import os

from MoinMoin.script import _util
from MoinMoin.script._util import MoinScript
from MoinMoin.request import RequestCLI
from MoinMoin.lupy import Index


class IndexScript(MoinScript):
    """ Lupy general index script class """

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--files", metavar="FILES", dest="file_list",
            help="filename of file list, e.g. files.lst (one file per line)"
        )
        self.parser.add_option(
            "--update", action="store_true", dest="update",
            help="when given, update an existing index"
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
    """ Lupy index build script class """

    def command(self):
        Index(self.request).indexPages(self.files, self.options.update)
        #Index(self.request).test(self.request)

        
