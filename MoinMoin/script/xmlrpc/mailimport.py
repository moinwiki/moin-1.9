# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MailImport script

    Imports a mail into the wiki.

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import sys
import xmlrpclib

from MoinMoin.script._util import MoinScript, fatal

input = sys.stdin

class PluginScript(MoinScript):
    """ Mail Importer """

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
    
    def mainloop(self):
        try:
            import mailimportconf
        except ImportError:
            fatal("Could not find the file mailimportconf.py. Maybe you want to use the config param?")

        secret = mailimportconf.mailimport_secret
        url = mailimportconf.mailimport_url
        
        s = xmlrpclib.ServerProxy(url)

        result = s.ProcessMail(secret, input.read())
        
        if result != "OK":
            print >>sys.stderr, result
