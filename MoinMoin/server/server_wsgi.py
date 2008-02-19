"""
    MoinMoin - WSGI application

    Minimal code for using this:

    import logging
    from MoinMoin.server.server_wsgi import WsgiConfig, moinmoinApp
    
    class Config(WsgiConfig):
        logPath = 'moin.log' # define your log file here
        #loglevel_file = logging.INFO # if you do not like the default

    config = Config() # you MUST create an instance to initialize logging!
    # use moinmoinApp here with your WSGI server / gateway

    @copyright: 2005 Anakim Border <akborder@gmail.com>,
                2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.server import Config
from MoinMoin.request import request_wsgi

class WsgiConfig(Config):
    """ WSGI default config """
    loglevel_stderr = None # we do not want to write to stderr!
         

def moinmoinApp(environ, start_response):
    request = request_wsgi.Request(environ)
    request.run()
    start_response(request.status, request.headers)
    return [request.output()]

