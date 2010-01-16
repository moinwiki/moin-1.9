# -*- coding: iso-8859-1 -*-
"""
MoinMoin - remote command execution, client part

@copyright: 2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

import sys
import xmlrpclib

from MoinMoin.script import MoinScript, fatal

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to execute moin scripts remotely.

Detailed Instructions:
======================
General syntax: moin [options] xmlrpc remote [remote-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[remote-options] see below:
    0. Verify that you have a remotescriptconf.py configuration file.

    1. To run the script 'account check' remotely.
       moin ... xmlrpc remote account check
"""

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
            print >> sys.stderr, result

