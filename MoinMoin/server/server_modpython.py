# -*- coding: iso-8859-1 -*-
"""
    MoinMoin.server.server_modpython

    This is not really a server, it is just so that modpython stuff
    (the real server is likely Apache2) fits the model we have for
    Twisted and standalone server.

    Minimal usage:

        from MoinMoin.server.server_modpython import CgiConfig, run

        class Config(CgiConfig):
            pass

        run(Config)

    See more options in CgiConfig class.

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.server import Config
from MoinMoin.request import request_modpython

# Set threads flag, so other code can use proper locking.
# TODO: It seems that modpy does not use threads, so we don't need to
# set it here. Do we have another method to check this?
from MoinMoin import config
config.use_threads = 1
del config

# Server globals
config = None

class ModpythonConfig(Config):
    """ Set up default server """
    properties = {}


def modpythonHandler(request, ConfigClass=ModpythonConfig):
    config = ConfigClass()
    moinreq = request_modpython.Request(request, config.properties)
    return moinreq.run(request)

