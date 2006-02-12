#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
MoinMoin - optimize lupy search engine's index

You must run this script as owner of the wiki files, usually this is the
web server user.

@copyright: 2005 by Florian Festi, Nir Soffer
@license: GNU GPL, see COPYING for details.
"""
doit = 1
import os

# Insert the path to MoinMoin in the start of the path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), 
                                os.pardir, os.pardir))

if not doit:
    print """
Until the following bug is closed, we avoid running this script:

http://moinmoin.wikiwikiweb.de/MoinMoinBugs/LupyOptimizeBreaksIndex

If you like, help us finding the problem.

Terminating now, doing NOTHING...
"""
    sys.exit(1)

from MoinMoin.scripts.moin_build_index import IndexScript
from MoinMoin.request import RequestCLI
from MoinMoin.lupy import Index


class OptimizeIndex(IndexScript):
    def command(self):
        Index(self.request).optimize()


def run():
    OptimizeIndex().run()

if __name__ == "__main__":
    run()

