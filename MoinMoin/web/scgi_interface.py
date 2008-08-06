# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SCGI interface

    @copyright: 2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import optparse

from MoinMoin.web.frontend import ServerFrontEnd

from MoinMoin import log
logging = log.getLogger(__name__)

class SCGIFrontEnd(ServerFrontEnd):
    def run_server(self, application, options):
        from flup.server.scgi import WSGIServer

        kwargs = {}
        if options.port:
            kwargs['bindAddress'] = (options.interface, options.port)
        elif options.interface.startswith('/') or \
                options.interface.startswith('./'):
            kwargs['bindAddress'] = options.interface

        WSGIServer(application, **kwargs).run()

def run():
    SCGIFrontEnd().run()

if __name__ == '__main__':
    run()
