# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - cli show script

    Just run a CLI request and show the output.

    @copyright: 2006 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.script._util import MoinScript

class PluginScript(MoinScript):
    """ show page script class """

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
    
    def mainloop(self):
        self.init_request()
        self.request.run()

