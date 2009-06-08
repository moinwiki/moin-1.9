# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CLI Request Implementation for commandline usage.

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.request import RequestBase, RemoteClosedConnection

class Request(RequestBase):
    """ specialized on command line interface and script requests """

    def __init__(self, url='CLI', pagename='', properties={}, given_config=None):
        self.saved_cookie = ''
        self.path_info = '/' + pagename
        self.query_string = ''
        self.remote_addr = '127.0.0.1'
        self.is_ssl = 0
        self.http_user_agent = 'CLI/Script'
        self.url = url
        self.request_method = 'GET'
        self.request_uri = '/' + pagename # TODO check if /pagename works as URI for CLI usage
        self.http_host = 'localhost'
        self.http_referer = ''
        self.script_name = '.'
        self.content_length = None
        self.if_modified_since = None
        self.if_none_match = None
        RequestBase.__init__(self, properties, given_config)
        self.cfg.caching_formats = [] # don't spoil the cache
        self.initTheme() # usually request.run() does this, but we don't use it

    def _setup_args_from_cgi_form(self):
        """ Override to create cli form """
        #form = cgi.FieldStorage()
        #return RequestBase._setup_args_from_cgi_form(self, form)
        return {}

    def read(self, n):
        """ Read from input stream. """
        if n is None:
            logging.warning("calling request.read(None) might block")
            return sys.stdin.read()
        else:
            return sys.stdin.read(n)

    def write(self, *data):
        """ Write to output stream. """
        data = self.encode(data)
        try:
            sys.stdout.write(data)
        except IOError:
            raise RemoteClosedConnection()

    def flush(self):
        sys.stdout.flush()

    def finish(self):
        RequestBase.finish(self)
        # flush the output, ignore errors caused by the user closing the socket
        try:
            sys.stdout.flush()
        except IOError, ex:
            import errno
            if ex.errno != errno.EPIPE:
                raise

    def isForbidden(self):
        """ Nothing is forbidden """
        return 0

    # Accessors --------------------------------------------------------

    def getQualifiedURL(self, uri=None):
        """ Return a full URL starting with schema and host

        TODO: does this create correct pages when you render wiki pages
              within a cli request?!
        """
        return uri

    # Headers ----------------------------------------------------------

    def setHttpHeader(self, header):
        pass

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        pass

    def http_redirect(self, url):
        """ Redirect to a fully qualified, or server-rooted URL

        TODO: Does this work for rendering redirect pages?
        """
        raise Exception("Redirect not supported for command line tools!")


