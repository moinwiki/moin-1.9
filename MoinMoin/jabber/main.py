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
from config import JabberConfig
from xmppbot import XMPPBot
from xmlrpcbot import XMLRPCServer, XMLRPCClient
from Queue import Queue

def main():
    commands_from_xmpp = Queue()
    commands_to_xmpp = Queue()
    
    try:
        xmpp_bot = XMPPBot(JabberConfig, commands_from_xmpp, commands_to_xmpp)
        xmlrpc_client = XMLRPCClient(commands_from_xmpp)
        xmlrpc_server = XMLRPCServer(commands_to_xmpp)
        
        xmpp_bot.start()
        xmlrpc_client.start()
        xmlrpc_server.start()
    
    except KeyboardInterrupt, i:
        print i
        sys.exit(0)

if __name__ == "__main__": main()