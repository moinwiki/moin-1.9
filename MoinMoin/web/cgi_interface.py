# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI/FCGI interface

    @copyright: 2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import optparse

from MoinMoin.web.frontend import ServerFrontEnd

from MoinMoin import log
logging = log.getLogger(__name__)

class CGIFrontEnd(ServerFrontEnd):
    def run_server(self, application, options):
        cgi_fallback = False

        try:
            from flup.server.fcgi import WSGIServer
        except ImportError:
            from MoinMoin.web._fallback_cgi import WSGIServer
            cgi_fallback = True

        kwargs = {}
        if options.port:
            kwargs['bindAddress'] = (options.interface, options.port)
        elif options.interface.startswith('/') or \
                options.interface.startswith('./'):
            kwargs['bindAddress'] = options.interface
        if not cgi_fallback:
            WSGIServer(application, **kwargs).run()
        else:
            if 'bindAddress' in kwargs:
                logging.warning('Cannot bind to socket when running with CGI fallback')
                WSGIServer(application).run()

def run():
    CGIFrontEnd().run()

if __name__ == '__main__':
    run()
