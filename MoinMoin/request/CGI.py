# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI Request Implementation for std. CGI web servers
    like Apache or IIS or others.

    @copyright: 2001-2003 by Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys, os, cgi

from MoinMoin.request import RequestBase

class Request(RequestBase):
    """ specialized on CGI requests """

    def __init__(self, properties={}):
        try:
            # force input/output to binary
            if sys.platform == "win32":
                import msvcrt
                msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
                msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

            self._setup_vars_from_std_env(os.environ)
            RequestBase.__init__(self, properties)

        except Exception, err:
            self.fail(err)

    def _setup_args_from_cgi_form(self):
        """ Override to create cgi form """
        form = cgi.FieldStorage()
        return RequestBase._setup_args_from_cgi_form(self, form)

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

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        for header in headers:
            self.write("%s\r\n" % header)
        self.write("\r\n")

