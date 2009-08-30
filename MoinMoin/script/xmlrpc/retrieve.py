# -*- coding: iso-8859-1 -*-
"""
MoinMoin - page contents retriever

@copyright: 2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

import xmlrpclib

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to print out the contents of a page via xmlrpc.

Detailed Instructions:
======================
General syntax: moin [options] xmlrpc retrieve [retrieve-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[retrieve-options] see below:
    0. To retrieve the page 'FrontPage' from the wiki '192.168.0.1' which is
       running xmlrpc
       moin ... xmlrpc retrieve 192.168.0.1 FrontPage
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.argv = argv

    def mainloop(self):
        s = xmlrpclib.ServerProxy(self.argv[0])
        print s.getPage(self.argv[1])
