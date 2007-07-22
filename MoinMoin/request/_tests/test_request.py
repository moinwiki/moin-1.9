# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.module_tested Tests

    Module names must start with 'test_' to be included in the tests.

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS
from MoinMoin import config, wikiutil

class TestNormalizePagename(unittest.TestCase):

    def testPageInvalidChars(self):
        """ request: normalize pagename: remove invalid unicode chars

        Assume the default setting
        """
        test = u'\u0000\u202a\u202b\u202c\u202d\u202e'
        expected = u''
        result = self.request.normalizePagename(test)
        self.assertEqual(result, expected,
                         ('Expected "%(expected)s" but got "%(result)s"') % locals())

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
            self.assertEqual(result, expected,
                             ('Expected "%(expected)s" but got "%(result)s"') %
                             locals())

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
            self.assertEqual(result, expected,
                             ('Expected "%(expected)s" but got "%(result)s"') %
                             locals())

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
            self.assertEqual(result, expected,
                             ('Expected "%(expected)s" but got "%(result)s"') %
                             locals())


class TestGroupPages(unittest.TestCase):

    def setUp(self):
        self.config = self.TestConfig(page_group_regex=r'.+Group')

    def tearDown(self):
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
                self.assertEqual(result, expected,
                                 ('Expected "%(expected)s" but got "%(result)s"') %
                                 locals())


class TestHTTPDate(unittest.TestCase):

    def testRFC1123Date(self):
        """ request: httpDate default rfc1123 """
        self.failUnlessEqual(self.request.httpDate(0),
                             'Thu, 01 Jan 1970 00:00:00 GMT',
                             'wrong date string')

    def testRFC850Date(self):
        """ request: httpDate rfc850 """
        self.failUnlessEqual(self.request.httpDate(0, rfc='850'),
                             'Thursday, 01-Jan-70 00:00:00 GMT',
                             'wrong date string')


coverage_modules = ['MoinMoin.request']

