# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI application


    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from werkzeug.utils import responder
from werkzeug.wrappers import Response

from MoinMoin.web.contexts import HTTPContext

def application(environ, start_response):
    request = HTTPContext(environ)
    request.run()

    response = Response(status=request.status,
                        headers=request.headers)

    if getattr(request, '_send_file', None) is not None:
        # moin wants to send a file (e.g. AttachFile.do_get)
        def simple_wrapper(fileobj, bufsize):
            return iter(lambda: fileobj.read(bufsize), '')
        file_wrapper = environ.get('wsgi.file_wrapper', simple_wrapper)
        response.response = file_wrapper(request._send_file, request._send_bufsize)
    else:
        response.response = request.output()
    return response

application = responder(application)
