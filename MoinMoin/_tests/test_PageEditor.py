# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.PageEditor Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS

import py

from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor


class TestExpandVars(unittest.TestCase):
    """PageEditor: testing page editor"""

    pagename = u'AutoCreatedMoinMoinTemporaryTestPage'

    _tests = (
        # Variable,             Expanded
        ("@PAGE@",              pagename),
        ("em@PAGE@bedded",      "em%sbedded" % pagename),
        ("@NOVAR@",             "@NOVAR@"),
        ("case@Page@sensitive", "case@Page@sensitive"),
        )

    def setUp(self):
        self.page = PageEditor(self.request, self.pagename)

    def testExpandVariables(self):
        """ PageEditor: expand general variables """
        for var, expected in self._tests:
            result = self.page._expand_variables(var)
            self.assertEqual(result, expected,
                'Expected "%(expected)s" but got "%(result)s"' % locals())


class TestExpandUserName(unittest.TestCase):
    """ Base class for user name tests

    Set user name during tests.
    """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPage'
    variable = u'@USERNAME@'

    def setUp(self):
        self.page = PageEditor(self.request, self.pagename)
        self.savedName = self.request.user.name
        self.request.user.name = self.name

    def tearDown(self):
        self.request.user.name = self.savedName

    def expand(self):
        return self.page._expand_variables(self.variable)


class TestExpandCamelCaseName(TestExpandUserName):

    name = u'UserName'

    def testExpandCamelCaseUserName(self):
        """ PageEditor: expand @USERNAME@ CamelCase """
        self.assertEqual(self.expand(), self.name)


class TestExpandExtendedName(TestExpandUserName):

    name = u'user name'

    def testExtendedNamesEnabled(self):
        """ PageEditor: expand @USERNAME@ extended name - enabled """
        try:
            config = self.TestConfig()
            self.assertEqual(self.expand(), u'["%s"]' % self.name)
        finally:
            del config


class TestExpandMailto(TestExpandUserName):

    variable = u'@MAILTO@'
    name = u'user name'
    email = 'user@example.com'

    def setUp(self):
        TestExpandUserName.setUp(self)
        self.savedValid = self.request.user.valid
        self.request.user.valid = 1
        self.savedEmail = self.request.user.email
        self.request.user.email = self.email

    def tearDown(self):
        TestExpandUserName.tearDown(self)
        self.request.user.valid = self.savedValid
        self.request.user.email = self.savedEmail

    def testMailto(self):
        """ PageEditor: expand @MAILTO@ """
        self.assertEqual(self.expand(), u'[[MailTo(%s)]]' % self.email)


class TestExpandPrivateVariables(TestExpandUserName):

    variable = u'@ME@'
    name = u'AutoCreatedMoinMoinTemporaryTestUser'
    dictPage = name + '/MyDict'
    shouldDeleteTestPage = True

    def setUp(self):
        TestExpandUserName.setUp(self)
        self.savedValid = self.request.user.valid
        self.request.user.valid = 1
        self.createTestPage()
        self.deleteCaches()

    def tearDown(self):
        TestExpandUserName.tearDown(self)
        self.request.user.valid = self.savedValid
        self.deleteTestPage()

    def testPrivateVariables(self):
        """ PageEditor: expand user variables """
        self.assertEqual(self.expand(), self.name)

    def createTestPage(self):
        """ Create temporary page, bypass logs, notification and backups

        TODO: this code is very fragile, any change in the
        implementation will break this test. Need to factor PageEditor
        to make it possible to create page without loging and notifying.
        """
        import os
        path = self.dictPagePath()
        if os.path.exists(path):
            self.shouldDeleteTestPage = False
            py.test.skip("%s exists. Won't overwrite exiting page" % self.dictPage)
        try:
            os.mkdir(path)
            revisionsDir = os.path.join(path, 'revisions')
            os.mkdir(revisionsDir)
            current = '00000001'
            file(os.path.join(path, 'current'), 'w').write('%s\n' % current)
            text = u' ME:: %s\n' % self.name
            file(os.path.join(revisionsDir, current), 'w').write(text)
        except Exception, err:
            py.test.skip("Can not be create test page: %s" % err)

    def deleteCaches(self):
        """ Force the wiki to scan the test page into the dicts """
        from MoinMoin import caching
        caching.CacheEntry(self.request, 'wikidicts', 'dicts_groups', scope='wiki').remove()
        if hasattr(self.request, 'dicts'):
            del self.request.dicts
        if hasattr(self.request.cfg, 'DICTS_DATA'):
            del self.request.cfg.DICTS_DATA
        self.request.pages = {}

    def deleteTestPage(self):
        """ Delete temporary page, bypass logs and notifications """
        if self.shouldDeleteTestPage:
            import shutil
            shutil.rmtree(self.dictPagePath(), True)

    def dictPagePath(self):
        page = Page(self.request, self.dictPage)
        return page.getPagePath(use_underlay=0, check_create=0)

