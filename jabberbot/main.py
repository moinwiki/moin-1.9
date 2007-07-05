# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot main file

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import logging, os, sys
from Queue import Queue

from jabberbot.config import BotConfig
from jabberbot.xmppbot import XMPPBot
from jabberbot.xmlrpcbot import XMLRPCServer, XMLRPCClient


def main():
    args = sys.argv

    if "--help" in args:
        print """MoinMoin notification bot

        Usage: %(myname)s [--server server] [--xmpp_port port] [--user user] [--resource resource] [--password pass] [--xmlrpc_host host] [--xmlrpc_port port]
        """ % {"myname": os.path.basename(args[0])}

        raise SystemExit

    log = logging.getLogger("log")
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())

    # TODO: actually accept options from the help string
    commands_from_xmpp = Queue()
    commands_to_xmpp = Queue()

    try:
        xmpp_bot = XMPPBot(BotConfig, commands_from_xmpp, commands_to_xmpp)
        xmlrpc_client = XMLRPCClient(BotConfig, commands_from_xmpp, commands_to_xmpp)
        xmlrpc_server = XMLRPCServer(BotConfig, commands_to_xmpp)

        xmpp_bot.start()
        xmlrpc_client.start()
        xmlrpc_server.start()

    except KeyboardInterrupt, i:
        print i
        sys.exit(0)


if __name__ == "__main__":
    main()
