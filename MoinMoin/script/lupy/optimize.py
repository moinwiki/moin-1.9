# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - optimize lupy search engine's index

    You must run this script as owner of the wiki files, usually this is the
    web server user.

    @copyright: 2005 by Florian Festi, Nir Soffer,
                2006 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""
doit = 0

from MoinMoin.script.lupy.build import IndexScript
from MoinMoin.lupy import Index

class PluginScript(IndexScript):
    def command(self):
        if doit:
            Index(self.request).optimize()
        else:
            print "See http://moinmoin.wikiwikiweb.de/MoinMoinBugs/LupyOptimizeBreaksIndex !"

