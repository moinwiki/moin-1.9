"""
    MoinMoin - WSGI application

    @copyright: 2005 Anakim Border <akborder@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.request import request_wsgi

def moinmoinApp(environ, start_response):
    request = request_wsgi.Request(environ)
    request.run()
    start_response(request.status, request.headers)
    return [request.output()]

