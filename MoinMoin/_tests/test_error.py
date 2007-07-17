# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.error Tests

    @copyright: 2003-2004 by Nir Soffer <nirs AT freeshell DOT org>
    @license: GNU GPL, see COPYING for details.
"""

import unittest # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS
from MoinMoin import error


class TestEncoding(unittest.TestCase):
    """ MoinMoin errors do work with unicode transparently """

    def testCreateWithUnicode(self):
        """ error: create with unicode """
        err = error.Error(u'טעות')
        self.assertEqual(unicode(err), u'טעות')
        self.assertEqual(str(err), 'טעות')

    def testCreateWithEncodedString(self):
        """ error: create with encoded string """
        err = error.Error('טעות')
        self.assertEqual(unicode(err), u'טעות')
        self.assertEqual(str(err), 'טעות')

    def testCreateWithObject(self):
        """ error: create with any object """
        class Foo:
            def __unicode__(self):
                return u'טעות'
            def __str__(self):
                return 'טעות'

        err = error.Error(Foo())
        self.assertEqual(unicode(err), u'טעות')
        self.assertEqual(str(err), 'טעות')

    def testAccessLikeDict(self):
        """ error: access error like a dict """
        test = 'value'
        err = error.Error(test)
        self.assertEqual('%(message)s' % err, test)

