"""
    MoinMoin - WSGI application

    Minimal code for using this:

    from MoinMoin.server.server_wsgi import WsgiConfig, moinmoinApp

    class Config(WsgiConfig):
        pass

    config = Config() # you MUST create an instance
    # use moinmoinApp here with your WSGI server / gateway

    @copyright: 2005 Anakim Border <akborder@gmail.com>,
                2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.server import Config
from MoinMoin.request import request_wsgi

class WsgiConfig(Config):
    """ WSGI default config """
    pass


def moinmoinApp(environ, start_response):
    request = request_wsgi.Request(environ)
    request.run()
    start_response(request.status, request.headers)
    return [request.output()]

