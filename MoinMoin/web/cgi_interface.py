# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI/FCGI interface

    @copyright: 2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import optparse

from MoinMoin.web.serving import make_application

from MoinMoin import log
logging = log.getLogger(__name__)


def run():
    parser = optparse.OptionParser()
    parser.add_option("-d", "--debug", action="store_true",
                      help="Enable debug mode of server (show tracebacks)")
    parser.add_option("-c", "--config-dir", dest="config_dir", metavar="DIR",
                      help=("Path to the directory containing the wiki "
                            "configuration files. Default: current directory"))
    parser.add_option("-p", "--port", dest="port", type="int",
                      help="Set the port to listen on. Act as CGI/FCGI script otherwise")
    parser.add_option("-i", "--interface", dest="interface",
                      help=("Set the interface/socket to listen on. If starts "
                            "with '/' or './' it is interpreted as a path "
                            "to a unix socket. Default: localhost"))
    parser.set_default('interface', 'localhost')

    try:
        from flup.server.fcgi import WSGIServer
    except ImportError:
        # TODO: insert some fallback here
        pass

    options, args = parser.parse_args()

    logging.debug('Options: %r', options)

    kwargs = {}
    if options.port:
        kwargs['bindAddress'] = (options.interface, options.port)
    elif options.interface.startswith('/') or \
            options.interface.startswith('./'):
        kwargs['bindAddress'] = options.interface

    app = make_application()
    WSGIServer(app, **kwargs).run()

if __name__ == '__main__':
    run()
