# -*- coding: iso-8859-1 -*-
"""
    MoinMoin.server.server_fastcgi

    This is not really a server, it is just so that fastcgi stuff
    (the real server is likely Apache2) fits the model we have for
    Twisted and standalone server.

    Minimal usage:

        from MoinMoin.server.server_fastcgi import FastCgiConfig, run

        class Config(FastCgiConfig):
            pass

        run(Config)

    See more options in FastCgiConfig class.

    @copyright: 2007 MoinMoin:ThomasWaldmann

    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.server import Config
from MoinMoin.request import request_fcgi
from MoinMoin.support import thfcgi

# Set threads flag, so other code can use proper locking.
from MoinMoin import config
config.use_threads = 1
del config

class FastCgiConfig(Config):
    """ Set up default server """
    properties = {}
    # properties = {'script_name': '/'}

    # how many requests shall be handled by a moin fcgi process before it dies,
    # -1 mean "unlimited lifetime":
    max_requests = -1

    # how many threads to use (1 means use only main program, non-threaded)
    max_threads = 5

    # backlog, use in socket.listen(backlog) call
    backlog = 5

    # default port
    port = None

def run(ConfigClass=FastCgiConfig):
    config = ConfigClass()

    handle_request = lambda req, env, form, properties=config.properties: \
                         request_fcgi.Request(req, env, form, properties=properties).run()
    fcg = thfcgi.FCGI(handle_request, port=config.port, max_requests=config.max_requests, backlog=config.backlog, max_threads=config.max_threads)
    fcg.run()

