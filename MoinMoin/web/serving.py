# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This module contains additional code related to serving
               requests with the standalone server. It uses werkzeug's
               BaseRequestHandler and overrides some functions that
               need to be handled different in MoinMoin than in werkzeug

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

from werkzeug.serving import BaseRequestHandler

from MoinMoin import version, log
logging = log.getLogger(__name__)

class RequestHandler(BaseRequestHandler):
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
