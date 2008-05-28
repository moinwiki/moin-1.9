# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI application


    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

from werkzeug.wrappers import Response
from werkzeug.debug import DebuggedApplication

from MoinMoin.web.request import Request


def application(request):
    request.run()
    response = Response(status=request.status,
                        headers=request.headers)
    if request._send_file is not None:
        # moin wants to send a file (e.g. AttachFile.do_get)
        def simple_wrapper(fileobj, bufsize):
            return iter(lambda: fileobj.read(bufsize), '')
        file_wrapper = environ.get('wsgi.file_wrapper', simple_wrapper)
        response.response = file_wrapper(request._send_file, request._send_bufsize)
    else:
        response.response = request.output()
    return response

application = Request.application(application)
application = DebuggedApplication(application)
