# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.util.pysupport Tests

    @copyright: 2004 Oliver Graf <ograf@bitart.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest, os, errno # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS

import py

from MoinMoin.util import pysupport


class TestImportNameFromMoin(unittest.TestCase):
    """ Test importName of MoinMoin modules

    We don't make any testing for files, assuming that moin package is
    not broken.
    """

    def testNonExistingModule(self):
        """ pysupport: import nonexistent module raises ImportError """
        self.assertRaises(ImportError, pysupport.importName,
                          'MoinMoin.parser.abcdefghijkl', 'Parser')

    def testNonExistingAttribute(self):
        """ pysupport: import nonexistent attritbue raises AttributeError """
        self.assertRaises(AttributeError, pysupport.importName,
                          'MoinMoin.parser.text_moin_wiki', 'NoSuchParser')

    def testExisting(self):
        """ pysupport: import name from existing module """
        from MoinMoin.parser import text_moin_wiki
        Parser = pysupport.importName('MoinMoin.parser.text_moin_wiki', 'Parser')
        self.failUnless(Parser is text_moin_wiki.Parser)


class TestImportNameFromPlugin(unittest.TestCase):
    """ Base class for import plugin tests """

    name = 'Parser'

    def setUp(self):
        """ Check for valid plugin package """
        self.pluginDirectory = os.path.join(self.request.cfg.data_dir, 'plugin', 'parser')
        self.checkPackage(self.pluginDirectory)
        self.pluginModule = (self.request.cfg.siteid + '.plugin.parser.' + self.plugin)

    def checkPackage(self, path):
        for item in (path, os.path.join(path, '__init__.py')):
            if not os.path.exists(item):
                py.test.skip("Missing or wrong permissions: %s" % item)

    def pluginExists(self):
        return (os.path.exists(self.pluginFilePath('.py')) or
                os.path.exists(self.pluginFilePath('.pyc')))

    def pluginFilePath(self, suffix):
        return os.path.join(self.pluginDirectory, self.plugin + suffix)


class TestImportNonExisiting(TestImportNameFromPlugin):

    plugin = 'NonExistingWikiPlugin'

    def testNonEsisting(self):
        """ pysupport: import nonexistent wiki plugin fail """
        if self.pluginExists():
            py.test.skip('plugin exists: %s' % self.plugin)
        self.assertRaises(ImportError, pysupport.importName,
                          self.pluginModule, self.name)


class TestImportExisting(TestImportNameFromPlugin):

    plugin = 'AutoCreatedMoinMoinTestPlugin'
    shouldDeleteTestPlugin = True

    def testExisting(self):
        """ pysupport: import existing wiki plugin

        Tests if a module can be imported from an arbitrary path
        like it is done in moin for plugins. Some strange bug
        in the old implementation failed on an import of os,
        cause os does a from os.path import that will stumble
        over a poisoned sys.modules.
        """
        try:
            self.createTestPlugin()
            plugin = pysupport.importName(self.pluginModule, self.name)
            self.assertEqual(getattr(plugin, '__name__', None), self.name,
                            'Failed to import the test plugin')
        finally:
            self.deleteTestPlugin()

    def createTestPlugin(self):
        """ Create test plugin, skiping if plugin exists """
        if self.pluginExists():
            self.shouldDeleteTestPlugin = False
            py.test.skip("Won't overwrite exiting plugin: %s" % self.plugin)
        data = '''
# If you find this file in your wiki plugin directory, you can safely
# delete it.
import sys, os

class Parser:
    pass
'''
        try:
            file(self.pluginFilePath('.py'), 'w').write(data)
        except Exception, err:
            py.test.skip("Can't create test plugin: %s" % str(err))

    def deleteTestPlugin(self):
        """ Delete plugin files ignoring missing files errors """
        if not self.shouldDeleteTestPlugin:
            return
        for suffix in ('.py', '.pyc'):
            try:
                os.unlink(self.pluginFilePath(suffix))
            except OSError, err:
                if err.errno != errno.ENOENT:
                    raise

