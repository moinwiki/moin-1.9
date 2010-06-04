# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.module_tested Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin import config, wikiutil
from MoinMoin._tests import wikiconfig

from MoinMoin.request import HeadersAlreadySentException

class TestNormalizePagename(object):

    def testPageInvalidChars(self):
        """ request: normalize pagename: remove invalid unicode chars

        Assume the default setting
        """
        test = u'\u0000\u202a\u202b\u202c\u202d\u202e'
        expected = u''
        result = self.request.normalizePagename(test)
        assert result == expected

    def testNormalizeSlashes(self):
        """ request: normalize pagename: normalize slashes """
        cases = (
            (u'/////', u''),
            (u'/a', u'a'),
            (u'a/', u'a'),
            (u'a/////b/////c', u'a/b/c'),
            (u'a b/////c d/////e f', u'a b/c d/e f'),
            )
        for test, expected in cases:
            result = self.request.normalizePagename(test)
            assert result == expected

    def testNormalizeWhitespace(self):
        """ request: normalize pagename: normalize whitespace """
        cases = (
            (u'         ', u''),
            (u'    a', u'a'),
            (u'a    ', u'a'),
            (u'a     b     c', u'a b c'),
            (u'a   b  /  c    d  /  e   f', u'a b/c d/e f'),
            # All 30 unicode spaces
            (config.chars_spaces, u''),
            )
        for test, expected in cases:
            result = self.request.normalizePagename(test)
            assert result == expected

    def testUnderscoreTestCase(self):
        """ request: normalize pagename: underscore convert to spaces and normalized

        Underscores should convert to spaces, then spaces should be
        normalized, order is important!
        """
        cases = (
            (u'         ', u''),
            (u'  a', u'a'),
            (u'a  ', u'a'),
            (u'a  b  c', u'a b c'),
            (u'a  b  /  c  d  /  e  f', u'a b/c d/e f'),
            )
        for test, expected in cases:
            result = self.request.normalizePagename(test)
            assert result == expected


class TestGroupPages(object):

    def testNormalizeGroupName(self):
        """ request: normalize pagename: restrict groups to alpha numeric Unicode

        Spaces should normalize after invalid chars removed!
        """
        cases = (
            # current acl chars
            (u'Name,:Group', u'NameGroup'),
            # remove than normalize spaces
            (u'Name ! @ # $ % ^ & * ( ) + Group', u'Name Group'),
            )
        for test, expected in cases:
            # validate we are testing valid group names
            if wikiutil.isGroupPage(self.request, test):
                result = self.request.normalizePagename(test)
                assert result == expected


class TestHTTPDate(object):

    def testRFC1123Date(self):
        """ request: httpDate default rfc1123 """
        assert self.request.httpDate(0) == 'Thu, 01 Jan 1970 00:00:00 GMT'

    def testRFC850Date(self):
        """ request: httpDate rfc850 """
        assert self.request.httpDate(0, rfc='850') == 'Thursday, 01-Jan-70 00:00:00 GMT'


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

