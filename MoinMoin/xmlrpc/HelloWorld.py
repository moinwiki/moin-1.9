# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This is just a sample for a xmlrpc plugin

    @copyright: 2005 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

def execute(xmlrpcobj, *args):
    text = args[0]
    return xmlrpcobj._outstr("Hello World!\n" + text)

