# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Standalone Moin Server Request Implementation

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import cgi

from MoinMoin.request import RequestBase

class Request(RequestBase):
    """ specialized on StandAlone Server (MoinMoin.server.standalone) requests """
    script_name = ''

    def __init__(self, sa, properties={}):
        """
        @param sa: stand alone server object
        @param properties: ...
        """
        try:
            self.sareq = sa
            self.wfile = sa.wfile
            self.rfile = sa.rfile
            self.headers = sa.headers
            self.is_ssl = 0

            # Copy headers
            self.http_accept_language = (sa.headers.getheader('accept-language')
                                         or self.http_accept_language)
            self.http_user_agent = sa.headers.getheader('user-agent', '')
            co = [c for c in sa.headers.getheaders('cookie') if c]
            self.saved_cookie = ', '.join(co) or ''
            self.if_modified_since = sa.headers.getheader('if-modified-since')
            self.if_none_match = sa.headers.getheader('if-none-match')

            # Copy rest from standalone request   
            self.server_name = sa.server.server_name
            self.server_port = str(sa.server.server_port)
            self.request_method = sa.command
            self.request_uri = sa.path
            self.remote_addr = sa.client_address[0]

            # Values that need more work                        
            self.path_info, self.query_string = self.splitURI(sa.path)
            self.setHttpReferer(sa.headers.getheader('referer'))
            self.setHost(sa.headers.getheader('host'))
            self.setURL(sa.headers)

            ##self.debugEnvironment(sa.headers)

            RequestBase.__init__(self, properties)

        except Exception, err:
            self.fail(err)

    def _setup_args_from_cgi_form(self):
        """ Override to create standalone form """
        form = cgi.FieldStorage(self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'})
        return RequestBase._setup_args_from_cgi_form(self, form)

    def read(self, n=None):
        """ Read from input stream
        
        Since self.rfile.read() will block, content-length will be used instead.
        
        TODO: test with n > content length, or when calling several times
        with smaller n but total over content length.
        """
        if n is None:
            try:
                n = int(self.headers.get('content-length'))
            except (TypeError, ValueError):
                import warnings
                warnings.warn("calling request.read() when content-length is "
                              "not available will block")
                return self.rfile.read()
        return self.rfile.read(n)

    def write(self, *data):
        """ Write to output stream. """
        self.wfile.write(self.encode(data))

    def flush(self):
        self.wfile.flush()

    def finish(self):
        RequestBase.finish(self)
        self.wfile.flush()

    # Headers ----------------------------------------------------------

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        st_header, other_headers = headers[0], headers[1:]
        status = st_header.split(':', 1)[1].lstrip()
        status_code, status_msg = status.split(' ', 1)
        status_code = int(status_code)
        self.sareq.send_response(status_code, status_msg)
        for header in other_headers:
            key, value = header.split(':', 1)
            value = value.lstrip()
            self.sareq.send_header(key, value)
        self.sareq.end_headers()

