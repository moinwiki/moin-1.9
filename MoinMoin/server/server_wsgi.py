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
    if request._send_file is not None:
        # moin wants to send a file (e.g. AttachFile.do_get)
        def simple_wrapper(fileobj, bufsize):
            return iter(lambda: fileobj.read(bufsize), '')
        file_wrapper = environ.get('wsgi.file_wrapper', simple_wrapper)
        return file_wrapper(request._send_file, request._send_bufsize)
    else:
        return [request.output()] # don't we have a filelike there also!?

