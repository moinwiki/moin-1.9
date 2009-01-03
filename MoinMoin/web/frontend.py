# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Common code for frontends (CGI/FCGI/SCGI)

    @copyright: 2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import optparse

from MoinMoin.web.serving import make_application

from MoinMoin import log
logging = log.getLogger(__name__)

class FrontEnd(object):
    def __init__(self):
        self.parser = optparse.OptionParser()
        self.add_options()

    def add_options(self):
        parser = self.parser
        parser.add_option("-d", "--debug", action="store_true",
                          help="Enable debug mode of server (show tracebacks)")
        parser.add_option("-c", "--config-dir", dest="config_dir", metavar="DIR",
                          help=("Path to the directory containing the wiki "
                                "configuration files. Default: current directory"))
        parser.add_option("--htdocs", dest="htdocs",
                          help=("Path to the directory containing Moin's "
                                "static files. Default: /usr/share/moin/htdocs"))
        parser.set_default('htdocs', '/usr/share/moin/htdocs')

    def run(self, args=None):
        options, args = self.parser.parse_args(args)
        logging.debug('Options: %r', options)

        if options.htdocs:
            application = make_application(shared=options.htdocs)
        else:
            application = make_application()

        try:
            self.run_server(application, options)
        except:
            logging.error('Error while running %s', self.__class__.__name__)
            raise

class ServerFrontEnd(FrontEnd):
    def add_options(self):
        super(ServerFrontEnd, self).add_options()
        parser = self.parser
        parser.add_option("-p", "--port", dest="port", type="int",
                          help="Set the port to listen on. Act as CGI/FCGI script otherwise")
        parser.add_option("-i", "--interface", dest="interface",
                          help=("Set the interface/socket to listen on. If starts "
                                "with '/' or './' it is interpreted as a path "
                                "to a unix socket. Default: localhost"))
        parser.set_default('interface', 'localhost')

class FrontEndNotAvailable(Exception):
    """ Raised if a frontend is not available for one reason or another. """
