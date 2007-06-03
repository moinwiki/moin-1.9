# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot main file

    This is a bot for notification and simple editing
    operations. Developed as a Google Summer of Code 
    project.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import sys
import os

from config import Config
from xmppbot import XMPPBot
from xmlrpcbot import XMLRPCServer, XMLRPCClient
from Queue import Queue


def main():
    args = sys.argv
    
    if "--help" in args:
        print """MoinMoin notification bot
        
        Usage: %(myname)s [--server server] [--xmpp_port port] [--user user] [--resource resource] [--password pass] [--xmlrpc_host host] [--xmlrpc_port port]
        """ % { "myname": os.path.basename(args[0]) }
        
        raise SystemExit
    
    # TODO: actually accept options from the help string

    commands_from_xmpp = Queue()
    commands_to_xmpp = Queue()
    
    try:
        xmpp_bot = XMPPBot(Config, commands_from_xmpp, commands_to_xmpp)
        xmlrpc_client = XMLRPCClient(Config, commands_from_xmpp)
        xmlrpc_server = XMLRPCServer(Config, commands_to_xmpp)
        
        xmpp_bot.start()
        xmlrpc_client.start()
        xmlrpc_server.start()
    
    except KeyboardInterrupt, i:
        print i
        sys.exit(0)

        
if __name__ == "__main__": main()
