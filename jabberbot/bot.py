#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot main file

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import logging, os, sys, time
from Queue import Queue

from jabberbot.config import BotConfig
from jabberbot.i18n import init_i18n
from jabberbot.xmppbot import XMPPBot
from jabberbot.xmlrpcbot import XMLRPCServer, XMLRPCClient


def _check_xmpp_version():
    """Checks if available version of pyxmpp is recent enough

    Since __revision__ is broken in current trunk, we can't rely on it.
    Therefore a simple check for known problems is used to determine if
    we can start the bot with it.

    """
    import pyxmpp

    msg = pyxmpp.message.Message()
    form = pyxmpp.jabber.dataforms.Form()

    try:
        msg.add_content(form)
    except TypeError:
        print 'Your version of pyxmpp is too old!'
        print 'You need a least revision 665 to run this bot. Exiting...'
        sys.exit(1)

def main():
    """Starts the jabber bot"""

    _check_xmpp_version()

    args = sys.argv
    if "--help" in args:
        print """MoinMoin notification bot

        Usage: %(myname)s [--server server] [--xmpp_port port] [--user user] [--resource resource] [--password pass] [--xmlrpc_host host] [--xmlrpc_port port]
        """ % {"myname": os.path.basename(args[0])}

        raise SystemExit

    log = logging.getLogger(__name__)
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.StreamHandler())

    init_i18n(BotConfig)

    # TODO: actually accept options from the help string
    commands_from_xmpp = Queue()
    commands_to_xmpp = Queue()

    xmpp_bot = None
    xmlrpc_client = None
    xmlrpc_server = None

    while True:
        try:
            if not xmpp_bot or not xmpp_bot.isAlive():
                log.info("(Re)starting XMPP thread...")
                xmpp_bot = XMPPBot(BotConfig, commands_from_xmpp, commands_to_xmpp)
                xmpp_bot.setDaemon(True)
                xmpp_bot.start()

            if not xmlrpc_client or not xmlrpc_client.isAlive():
                log.info("(Re)starting XMLRPC client thread...")
                xmlrpc_client = XMLRPCClient(BotConfig, commands_from_xmpp, commands_to_xmpp)
                xmlrpc_client.setDaemon(True)
                xmlrpc_client.start()

            if not xmlrpc_server or not xmlrpc_server.isAlive():
                log.info("(Re)starting XMLRPC server thread...")
                xmlrpc_server = XMLRPCServer(BotConfig, commands_to_xmpp)
                xmlrpc_server.setDaemon(True)
                xmlrpc_server.start()

            time.sleep(5)

        except KeyboardInterrupt, i:
            xmpp_bot.stop()
            xmlrpc_client.stop()

            log.info("Stopping XMPP bot thread, please wait...")
            xmpp_bot.join(5)
            log.info("Stopping XMLRPC client thread, please wait...")
            xmlrpc_client.join(5)

            sys.exit(0)


if __name__ == "__main__":
    main()
