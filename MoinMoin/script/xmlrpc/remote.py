# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - remote command execution, client part

    This can be used as client to execute moin scripts remotely.

    @copyright: 2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import sys
import xmlrpclib

from MoinMoin.script import MoinScript, fatal

class PluginScript(MoinScript):
    """ Remote Script Execution Client """

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.argv = argv

    def mainloop(self):
        try:
            import remotescriptconf as conf
        except ImportError:
            fatal("Could not find the file remotescriptconf.py. Maybe you want to use the config param?")

        secret = conf.remotescript_secret
        url = conf.remotescript_url
        print url, secret, self.argv

        s = xmlrpclib.ServerProxy(url)

        # TODO handle stdin 
        # xmlrpclib.Binary(sys.stdin.read())
        result = s.RemoteScript(secret, self.argv)
        # TODO handle stdout, stderr

        if result != "OK":
            print >>sys.stderr, result

