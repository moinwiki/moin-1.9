# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Standalone Moin Server Request Implementation

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import cgi
import socket
import errno

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.request import RequestBase, RemoteClosedConnection

# socket errors we just map to RemoteClosedConnection:
socket_errors = [errno.ECONNABORTED, errno.ECONNRESET,
                 errno.EPIPE, ]


class Request(RequestBase):
    """ specialized on StandAlone Server (MoinMoin.server.server_standalone) requests """
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
            try:
                self.content_length = int(sa.headers.getheader('content-length'))
            except (TypeError, ValueError):
                self.content_length = None
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
        form = cgi.FieldStorage(self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST'},
                                keep_blank_values=1)
        return RequestBase._setup_args_from_cgi_form(self, form)

    def read(self, n):
        """ Read from input stream """
        if n is None:
            logging.warning("calling request.read(None) might block")
            return self.rfile.read()
        else:
            return self.rfile.read(n)

    def write(self, *data):
        """ Write to output stream. """
        data = self.encode(data)
        try:
            self.wfile.write(data)
        except socket.error, err:
            if err.args[0] in socket_errors:
                raise RemoteClosedConnection()
            raise

    def flush(self):
        try:
            self.wfile.flush()
        except socket.error, err:
            if err.args[0] in socket_errors:
                raise RemoteClosedConnection()
            raise

    def finish(self):
        RequestBase.finish(self)
        self.flush()

    # Headers ----------------------------------------------------------

    def _emit_http_headers(self, headers):
        """ private method to send out preprocessed list of HTTP headers """
        st_header, other_headers = headers[0], headers[1:]
        status = st_header.split(':', 1)[1].lstrip()
        status_code, status_msg = status.split(' ', 1)
        status_code = int(status_code)
        try:
            self.sareq.send_response(status_code, status_msg)
            for header in other_headers:
                key, value = header.split(':', 1)
                value = value.lstrip()
                self.sareq.send_header(key, value)
            self.sareq.end_headers()
        except socket.error, err:
            if err.args[0] in socket_errors:
                raise RemoteClosedConnection()
            raise

