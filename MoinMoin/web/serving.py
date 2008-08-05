# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This module contains additional code related to serving
               requests with the standalone server. It uses werkzeug's
               BaseRequestHandler and overrides some functions that
               need to be handled different in MoinMoin than in werkzeug

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import os
from MoinMoin import config
from werkzeug.utils import SharedDataMiddleware
from werkzeug.serving import BaseRequestHandler, run_simple

from MoinMoin import version, log
logging = log.getLogger(__name__)

class RequestHandler(BaseRequestHandler):
    """
    A request-handler for WSGI, that overrides the default logging
    mechanisms to log via MoinMoin's logging framework.
    """
    server_version = "MoinMoin %s %s" % (version.release,
                                         version.revision)

    # override the logging functions
    def log_request(self, code='-', size='-'):
        self.log_message('"%s" %s %s',
                         self.requestline, code, size)

    def log_error(self, format, *args):
        self.log_message(format, *args)

    def log_message(self, format, *args):
        logging.info("%s %s", self.address_string(), (format % args))

class ProxyTrust(object):
    """
    Middleware that rewrites the remote address according to trusted
    proxies in the forward chain.
    """

    def __init__(self, app, proxies):
        self.app = app
        self.proxies = proxies

    def __call__(environ, start_response):
        if 'HTTP_X_FORWARDED_FOR' in environ:
            addrs = environ.pop('HTTP_X_FORWARDED_FOR').split(',')
            addrs = [x.strip() for addr in addrs]
        elif 'REMOTE_ADDR' in environ:
            addrs = [environ['REMOTE_ADDR']]
        else:
            addrs = [None]
        result = [addr for addr in addrs if addr not in self.proxies]
        if result:
            environ['REMOTE_ADDR'] = result[-1]
        elif addrs[-1] is not None:
            environ['REMOTE_ADDR'] = addrs[-1]
        else:
            del environ['REMOTE_ADDR']
        return self.app(environ, start_response)

def make_application(shared=None):
    from MoinMoin.wsgiapp import application

    if isinstance(shared, dict):
        application = SharedDataMiddleware(application, shared)
    elif shared:
        if shared is True:
            shared = '/use/share/moin/htdocs'

        if os.path.isdir(shared):
            mapping = {config.url_prefix_static: shared,
                       '/favicon.ico': os.path.join(shared, 'favicon.ico'),
                       '/robots.txt': os.path.join(shared, 'robots.txt')}
            application = SharedDataMiddleware(application, mapping)

    return application

def run_server(host='localhost', port=8080, docs='/usr/share/moin/htdocs',
               threaded=True, use_debugger=False):
    """ Run a standalone server on specified host/port. """
    application = make_application(shared=docs)

    run_simple(host, port, application, threaded=threaded,
               use_debugger=use_debugger,
               request_handler=RequestHandler)

