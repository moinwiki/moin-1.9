# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI Request Implementation for std. WSGI web servers.

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import cgi, StringIO

from MoinMoin.request import RequestBase, RemoteClosedConnection

class Request(RequestBase):
    """ specialized on WSGI requests """
    def __init__(self, env):
        try:
            self.env = env
            self.hasContentType = False

            self.stdin = env['wsgi.input']
            self.stdout = StringIO.StringIO()

            # used by MoinMoin.server.server_wsgi:
            self.status = '200 OK'
            self.headers = []

            self._setup_vars_from_std_env(env)
            RequestBase.__init__(self, {})

        except Exception, err:
            self.fail(err)

    def _setup_args_from_cgi_form(self):
        """ Override to create cgi form """
        form = cgi.FieldStorage(fp=self.stdin, environ=self.env, keep_blank_values=1)
        return RequestBase._setup_args_from_cgi_form(self, form)

    def read(self, n=None):
        if n is None:
            # We can't do that, because wsgi 1.0 requires n:
            #return self.stdin.read()
            # Thus, if we have no n, we have to simulate the usual behaviour (or
            # it won't work e.g. with mod_wsgi 1.3 and maybe other wsgi 1.0 servers).
            # Note: just requesting a extremely large amount (expecting it to never
            # be reached, but still all data returned) also does not work (mod_wsgi
            # 1.3 gives a MemoryError when doing that):
            data = []
            while True:
                read_data = self.stdin.read(4000)
                if not read_data:
                    break
                data.append(read_data)
            return ''.join(data)
        else:
            return self.stdin.read(n)

    def write(self, *data):
        data = self.encode(data)
        try:
            self.stdout.write(data)
        except Exception:
            raise RemoteClosedConnection()

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

    def output(self):
        # called by MoinMoin.server.server_wsgi
        return self.stdout.getvalue()


