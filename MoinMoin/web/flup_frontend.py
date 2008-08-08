# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Flup based WSGI adapters

    @copyright: 2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.web.frontend import ServerFrontEnd

from MoinMoin import log
logging = log.getLogger(__name__)

class FlupFrontEnd(ServerFrontEnd):

    is_fcgi = False

    def add_options(self):
        super(FlupFrontEnd, self).add_options()
        parser = self.parser
        parser.add_option("--min-spare", dest="min_spare", type="int", metavar='MIN',
                          help=("Minimum spare threads/processes (when "
                                "using threaded or forking servers)."))
        parser.add_option("--max-spare", dest="max_spare", type="int", metavar='MAX',
                          help=("Maximum spare threads/processes (when "
                                "using threaded or forking servers)."))
        parser.add_option("--max-childs", dest="max_childs", type="int", metavar='CHILDS',
                          help=("Hard upper limit on threads/processes "
                                "(when using threaded or forking servers)."))
        parser.add_option("-t", "--type", dest="server_type", metavar='TYPE',
                          help=("Type of server to use, e.g. single/threaded"
                                "/forking. Defaults to 'single' when not "
                                "bound to a socket and to 'threaded' when it is"))

    def run_server(self, application, options):
        cgi_fallback = False

        server_type = options.server_type

        if not server_type:
            server_type = (options.port and 'threaded') or 'single'

        if server_type not in self.server_types:
            raise ArgumentError("Unknown server type '%s'" % options.server_type)

        multi = server_type in ('threaded', 'forking')

        try:
            mod = self.server_types[server_type]
            mod = __import__(mod, fromlist=['WSGIServer'])
            WSGIServer = mod.WSGIServer
        except ImportError:
            if self.is_fcgi:
                from MoinMoin.web._fallback_cgi import WSGIServer
                cgi_fallback = True

        kwargs = {}

        if options.port:
            kwargs['bindAddress'] = (options.interface, options.port)
        elif options.interface.startswith('/') or \
                options.interface.startswith('./'):
            kwargs['bindAddress'] = options.interface

        if options.min_spare and multi:
            kwargs['minSpare'] = options.min_spare
        if options.max_spare and multi:
            kwargs['maxSpare'] = options.max_spare
        if options.max_childs and multi:
            if server_type == 'threaded':
                kwargs['maxThreads'] = options.max_childs
            else:
                kwargs['maxChildren'] = options.max_childs

        if not cgi_fallback:
            return WSGIServer(application, **kwargs).run()
        else:
            logging.warning('Running as CGI fallback.')
            return WSGIServer(application).run()

class FCGIFrontEnd(FlupFrontEnd):
    is_fcgi = True
    server_types = {'threaded': 'flup.server.fcgi',
                    'forking': 'flup.server.fcgi_fork',
                    'single': 'flup.server.fcgi_single'}

class SCGIFrontEnd(FlupFrontEnd):
    server_types = {'threaded': 'flup.server.scgi',
                    'forking': 'flup.server.scgi_fork'}

class AJPFrontEnd(FlupFrontEnd):
    server_types = {'threaded': 'flup.server.ajp',
                    'forking': 'flup.server.ajp_fork'}
