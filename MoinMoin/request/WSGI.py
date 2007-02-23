# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI Request Implementation for std. WSGI web servers.

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import cgi, StringIO

from MoinMoin.request import RequestBase

class Request(RequestBase):
    """ specialized on WSGI requests """
    def __init__(self, env):
        try:
            self.env = env
            self.hasContentType = False

            self.stdin = env['wsgi.input']
            self.stdout = StringIO.StringIO()

            # used by MoinMoin.server.wsgi:
            self.status = '200 OK'
            self.headers = []

            self._setup_vars_from_std_env(env)
            RequestBase.__init__(self, {})

        except Exception, err:
            self.fail(err)

    def setup_args(self):
        # TODO: does this include query_string args for POST requests?
        # see also how CGI works now
        form = cgi.FieldStorage(fp=self.stdin, environ=self.env, keep_blank_values=1)
        return RequestBase._setup_args_from_cgi_form(self, form)

    def read(self, n=None):
        if n is None:
            return self.stdin.read()
        else:
            return self.stdin.read(n)

    def write(self, *data):
        self.stdout.write(self.encode(data))

    def reset_output(self):
        self.stdout = StringIO.StringIO()

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        st_header, other_headers = headers[0], headers[1:]
        self.status = st_header.split(':', 1)[1].lstrip()
        for header in other_headers:
            key, value = header.split(':', 1)
            value = value.lstrip()
            self.headers.append((key, value))

    def flush(self):
        pass

    def finish(self):
        pass

    def output(self):
        # called by MoinMoin.server.wsgi
        return self.stdout.getvalue()


