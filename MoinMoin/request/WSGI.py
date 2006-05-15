# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI Request Implementation for std. WSGI web servers.

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys, os

from MoinMoin.request import RequestBase

class Request(RequestBase):
    """ specialized on WSGI requests """
    def __init__(self, env):
        try:
            self.env = env
            self.hasContentType = False
            
            self.stdin = env['wsgi.input']
            self.stdout = StringIO.StringIO()
            
            self.status = '200 OK'
            self.headers = []
            
            self._setup_vars_from_std_env(env)
            RequestBase.__init__(self, {})

        except Exception, err:
            self.fail(err)
    
    def setup_args(self, form=None):
        # TODO: does this include query_string args for POST requests?
        # see also how CGI works now
        if form is None:
            form = cgi.FieldStorage(fp=self.stdin, environ=self.env, keep_blank_values=1)
        return self._setup_args_from_cgi_form(form)
    
    def read(self, n=None):
        if n is None:
            return self.stdin.read()
        else:
            return self.stdin.read(n)
    
    def write(self, *data):
        self.stdout.write(self.encode(data))
    
    def reset_output(self):
        self.stdout = StringIO.StringIO()
    
    def setHttpHeader(self, header):
        if type(header) is unicode:
            header = header.encode('ascii')
        
        key, value = header.split(':', 1)
        value = value.lstrip()
        if key.lower() == 'content-type':
            # save content-type for http_headers
            if self.hasContentType:
                # we only use the first content-type!
                return
            else:
                self.hasContentType = True
        
        elif key.lower() == 'status':
            # save status for finish
            self.status = value
            return
            
        self.headers.append((key, value))
    
    def http_headers(self, more_headers=[]):
        for header in more_headers:
            self.setHttpHeader(header)
        
        if not self.hasContentType:
            self.headers.insert(0, ('Content-Type', 'text/html;charset=%s' % config.charset))
    
    def flush(self):
        pass
    
    def finish(self):
        pass
    
    def output(self):
        return self.stdout.getvalue()


