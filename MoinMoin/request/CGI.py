# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI Request Implementation for std. CGI web servers
    like Apache or IIS or others.

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys, os

from MoinMoin import config
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

    def open_logs(self):
        # create log file for catching stderr output
        if not self.opened_logs:
            sys.stderr = open(os.path.join(self.cfg.data_dir, 'error.log'), 'at')
            self.opened_logs = 1

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

    # Headers ----------------------------------------------------------

    def http_headers(self, more_headers=[]):
        # Send only once
        if getattr(self, 'sent_headers', None):
            return

        self.sent_headers = 1
        have_ct = 0

        # send http headers
        for header in more_headers + getattr(self, 'user_headers', []):
            if header.lower().startswith("content-type:"):
                # don't send content-type multiple times!
                if have_ct: continue
                have_ct = 1
            if type(header) is unicode:
                header = header.encode('ascii')
            self.write("%s\r\n" % header)

        if not have_ct:
            self.write("Content-type: text/html;charset=%s\r\n" % config.charset)

        self.write('\r\n')

        #from pprint import pformat
        #sys.stderr.write(pformat(more_headers))
        #sys.stderr.write(pformat(self.user_headers))


