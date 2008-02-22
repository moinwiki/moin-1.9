# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - page contents retriever

    @copyright: 2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

import xmlrpclib

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.argv = argv

    def mainloop(self):
        s = xmlrpclib.ServerProxy(self.argv[0])
        print s.getPage(self.argv[1])
