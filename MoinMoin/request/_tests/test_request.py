# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.module_tested Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin import config, wikiutil

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

    def setup_method(self, method):
        self.config = self.TestConfig(page_group_regex=r'.+Group')

    def teardown_method(self, method):
        del self.config

    def testNormalizeGroupName(self):
        """ request: normalize pagename: restrict groups to alpha numeric Unicode

        Spaces should normalize after invalid chars removed!
        """
        import re
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


coverage_modules = ['MoinMoin.request']

