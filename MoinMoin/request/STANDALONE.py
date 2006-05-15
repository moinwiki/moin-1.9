# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Standalone Moin Server Request Implementation

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys, os

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
            co = filter(None, sa.headers.getheaders('cookie'))
            self.saved_cookie = ', '.join(co) or ''
            
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

    def _setup_args_from_cgi_form(self, form=None):
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

    def http_headers(self, more_headers=[]):
        if getattr(self, 'sent_headers', None):
            return
        
        self.sent_headers = 1
        user_headers = getattr(self, 'user_headers', [])
        
        # check for status header and send it
        our_status = 200
        for header in more_headers + user_headers:
            if header.lower().startswith("status:"):
                try:
                    our_status = int(header.split(':', 1)[1].strip().split(" ", 1)[0]) 
                except:
                    pass
                # there should be only one!
                break
        # send response
        self.sareq.send_response(our_status)

        # send http headers
        have_ct = 0
        for header in more_headers + user_headers:
            if type(header) is unicode:
                header = header.encode('ascii')
            if header.lower().startswith("content-type:"):
                # don't send content-type multiple times!
                if have_ct: continue
                have_ct = 1

            self.write("%s\r\n" % header)

        if not have_ct:
            self.write("Content-type: text/html;charset=%s\r\n" % config.charset)

        self.write('\r\n')

        #from pprint import pformat
        #sys.stderr.write(pformat(more_headers))
        #sys.stderr.write(pformat(self.user_headers))

