# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot configuration file

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""


class BotConfig:
    # Node name (a valid JID) to be used
    xmpp_node = u"moinbot@jabber.example2.org/wiki"

    # Server to be used
    xmpp_server = u"jabber.example.com"

    # Port to connect to or None, if default
    xmpp_port = None

    # Password used to connect to the xmpp server
    xmpp_password = u""

    # Status message that the bot should set
    xmpp_status = u"Ready to serve!"

    # Set to True if bot should be verbose about actions it
    # is performing. Useful for debuging.
    verbose = True

    # Interface to listen on for XML RPC traffic
    xmlrpc_host = u"localhost"

    # Port to listen on for XML RPC traffic
    xmlrpc_port = 8000

    # Url where wiki is located (for reverse XML RPC traffic)
    wiki_url = u"http://localhost:8080/"

    # A secret shared with Wiki , must be the same in both
    # configs for communication to work.
    secret = "use the same string as in secrets setting in wiki config"


    # Maximum number of items in service discovery cache (XEP-0115)
    disco_cache_size = 100

    # Time allowed for a response for disco#info query (in seconds)
    disco_answering_timeout = 60
