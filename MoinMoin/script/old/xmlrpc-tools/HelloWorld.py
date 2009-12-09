#!/usr/bin/env python
"""
This script is a sample for xmlrpc calls.

It calls the HelloWorld.py xmlrpc plugin.

GPL software, 2003-08-10 Thomas Waldmann
"""

def run():
    import xmlrpclib
    srcwiki = xmlrpclib.ServerProxy("http://master.moinmo.in/?action=xmlrpc2")
    print srcwiki.HelloWorld("Hello Wiki User!\n")

if __name__ == "__main__":
    run()

