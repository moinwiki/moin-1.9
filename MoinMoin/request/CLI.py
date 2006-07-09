# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CLI Request Implementation for commandline usage.

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys, os

from MoinMoin.request import RequestBase

class Request(RequestBase):
    """ specialized on command line interface and script requests """

    def __init__(self, url='CLI', pagename='', properties={}):
        self.saved_cookie = ''
        self.path_info = '/' + pagename
        self.query_string = ''
        self.remote_addr = '127.0.0.1'
        self.is_ssl = 0
        self.http_user_agent = 'CLI/Script'
        self.url = url
        self.request_method = 'GET'
        self.request_uri = '/' + pagename # TODO check
        self.http_host = 'localhost'
        self.http_referer = ''
        self.script_name = '.'
        RequestBase.__init__(self, properties)
        self.cfg.caching_formats = [] # don't spoil the cache
        self.initTheme() # usually request.run() does this, but we don't use it
  
    def read(self, n=None):
        """ Read from input stream. """
        if n is None:
            return sys.stdin.read()
        else:
            return sys.stdin.read(n)

    def write(self, *data):
        """ Write to output stream. """
        sys.stdout.write(self.encode(data))

    def flush(self):
        sys.stdout.flush()
        
    def finish(self):
        RequestBase.finish(self)
        # flush the output, ignore errors caused by the user closing the socket
        try:
            sys.stdout.flush()
        except IOError, ex:
            import errno
            if ex.errno != errno.EPIPE: raise

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

    def http_headers(self, more_headers=[]):
        pass

    def http_redirect(self, url):
        """ Redirect to a fully qualified, or server-rooted URL 
        
        TODO: Does this work for rendering redirect pages?
        """
        raise Exception("Redirect not supported for command line tools!")


