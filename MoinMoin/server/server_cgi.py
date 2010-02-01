# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI pseudo Server

    This is not really a server, it is just so that CGI stuff (the real
    server is likely Apache or IIS or some other std. CGI server) looks
    similar to what we have for Twisted and standalone server.

    Minimal usage:

        from MoinMoin.server.server_cgi import CgiConfig, run

        class Config(CgiConfig):
            pass

        run(Config)

    See more options in CgiConfig class.

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.server import Config
from MoinMoin.request import request_cgi

# Server globals
config = None

# ------------------------------------------------------------------------
# Public interface

class CgiConfig(Config):
    """ CGI default config """
    name = 'moin'
    properties = {}

    # Development options
    hotshotProfile = None # e.g. "moin.prof"


def run(configClass):
    """ Create and run a Cgi Request

    See CgiConfig for available options

    @param configClass: config class
    """

    config = configClass()

    if config.hotshotProfile:
        import hotshot
        config.hotshotProfile = hotshot.Profile(config.hotshotProfile)
        config.hotshotProfile.start()

    request = request_cgi.Request(properties=config.properties)
    request.run()

    if config.hotshotProfile:
        config.hotshotProfile.close()


