# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.module_tested Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin import config, wikiutil

from MoinMoin.request import HeadersAlreadySentException

class TestHTTPHeaders(object):
    std_headers = ['Status: 200 OK', 'Content-type: text/html; charset=%s' % config.charset]

    def setup_method(self, method):
        self.request.sent_headers = None

    def testAutoAddStdHeaders(self):
        """ test if the usual headers get auto-added if not specified """
        headers_out = self.request.emit_http_headers(testing=True)
        assert headers_out == self.std_headers

    def testHeadersOnlyOnce(self):
        """ test if trying to call emit_http_headers multiple times raises an exception """
        self.request.emit_http_headers(testing=True)
        py.test.raises(HeadersAlreadySentException, self.request.emit_http_headers, [], {'testing': True})

    def testDuplicateHeadersIgnored(self):
        """ test if duplicate headers get ignored """
        headers_in = self.std_headers + ['Status: 500 Server Error']
        headers_expected = self.std_headers
        headers_out = self.request.emit_http_headers(headers_in, testing=True)
        assert headers_out == headers_expected

    def testListHeaders(self):
        """ test if header values get merged into a list for headers supporting it """
        headers_in = self.std_headers + ['Vary: aaa', 'vary: bbb']
        headers_expected = self.std_headers + ['Vary: aaa, bbb']
        headers_out = self.request.emit_http_headers(headers_in, testing=True)
        assert headers_out == headers_expected

coverage_modules = ['MoinMoin.request']

