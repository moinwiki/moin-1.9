# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Fallback CGI WSGI interface

    Provide a simple WSGI-to-CGI adapter in case flup is not available.
    It is taken from http://www.python.org/dev/peps/pep-0333/.

    @copyright: 2003-2006 Phillip J. Eby <pje at telecommunity.com>
    @license: Public Domain
"""
import os, sys


__all__ = ['WSGIServer']


class WSGIServer(object):

    def __init__(self, application):
        self.application = application

    def run(self):

        environ = dict(os.environ.items())
        environ['wsgi.input']        = sys.stdin
        environ['wsgi.errors']       = sys.stderr
        environ['wsgi.version']      = (1, 0)
        environ['wsgi.multithread']  = False
        environ['wsgi.multiprocess'] = True
        environ['wsgi.run_once']     = True

        if environ.get('HTTPS', 'off') in ('on', '1'):
            environ['wsgi.url_scheme'] = 'https'
        else:
            environ['wsgi.url_scheme'] = 'http'

        headers_set = []
        headers_sent = []

        def write(data):
            if not headers_set:
                raise AssertionError("write() before start_response()")

            elif not headers_sent:
                # Before the first output, send the stored headers
                status, response_headers = headers_sent[:] = headers_set
                sys.stdout.write('Status: %s\r\n' % status)
                for header in response_headers:
                    sys.stdout.write('%s: %s\r\n' % header)
                sys.stdout.write('\r\n')

            sys.stdout.write(data)
            sys.stdout.flush()

        def start_response(status, response_headers, exc_info=None):
            if exc_info:
                try:
                    if headers_sent:
                        # Re-raise original exception if headers sent
                        raise exc_info[0], exc_info[1], exc_info[2]
                finally:
                    exc_info = None     # avoid dangling circular ref
            elif headers_set:
                raise AssertionError("Headers already set!")

            headers_set[:] = [status, response_headers]
            return write

        result = self.application(environ, start_response)
        try:
            for data in result:
                if data:    # don't send headers until body appears
                    write(data)
            if not headers_sent:
                write('')   # send headers now if body was empty
        finally:
            if hasattr(result, 'close'):
                result.close()
