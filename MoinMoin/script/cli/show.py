# -*- coding: iso-8859-1 -*-
"""
MoinMoin - cli show script

@copyright: 2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script import MoinScript
from MoinMoin.wsgiapp import run

class PluginScript(MoinScript):
    """\
Purpose:
========
Just run a CLI request and show the output.

Detailed Instructions:
======================
General syntax: moin [options] cli show

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def mainloop(self):
        self.init_request()
        run(self.request)
