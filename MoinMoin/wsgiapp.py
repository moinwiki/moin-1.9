# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI application

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from werkzeug.utils import responder
from werkzeug.wrappers import Response
from werkzeug.exceptions import NotFound

from MoinMoin.web.contexts import HTTPContext, RenderContext
from MoinMoin.web.request import Request
from MoinMoin.web.utils import check_spider, check_forbidden, check_setuid
from MoinMoin.web.utils import check_surge_protect, handle_auth_form
from MoinMoin.web.apps import HTTPExceptionsMiddleware

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil, user, caching, error
from MoinMoin.action import get_names, get_available_actions
from MoinMoin.config import multiconfig
from MoinMoin.support.python_compatibility import set
from MoinMoin.util import IsWin9x
from MoinMoin.util.clock import Clock
from MoinMoin import auth

def _request_init(request):
    request.clock = Clock()
    request.clock.start('total')
    request.clock.start('base__init__')

    user_obj = request.cfg.session_handler.start(request, request.cfg.session_id_handler)
    request.user = handle_auth_form(user_obj, request)

    request.cfg.session_handler.after_auth(request, request.cfg.session_id_handler, request.user)

    if not request.user:
        request.user = user.User(request, auth_method='request:invalid')

    check_setuid(request)

    request = RenderContext(request)

    if request.action != 'xmlrpc':
        check_forbidden(request)
        check_surge_protect(request)

    request.reset()

    request.clock.stop('base__init__')
    return request

def application(environ, start_response):
    request = Request(environ)
    request = HTTPContext(request)
    request = _request_init(request)
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
application = HTTPExceptionsMiddleware(application)
