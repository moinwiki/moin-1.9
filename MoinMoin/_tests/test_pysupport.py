# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.util.pysupport Tests

    @copyright: 2004 by Jürgen Hermann <ograf@bitart.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest, os, errno
from MoinMoin.util import pysupport
from MoinMoin._tests import TestSkiped


class ImportNameFromMoinTestCase(unittest.TestCase):
    """ Test importName of MoinMoin modules

    We don't make any testing for files, assuming that moin package is
    not broken.
    """

    def testNonExistingModule(self):
        """ pysupport: import nonexistent module raises ImportError """
        self.assertRaises(ImportError, pysupport.importName,
                          'MoinMoin.parser.abcdefghijkl','Parser')

    def testNonExistingAttribute(self):
        """ pysupport: import nonexistent attritbue raises AttributeError """
        self.assertRaises(AttributeError, pysupport.importName,
                          'MoinMoin.parser.wiki','NoSuchParser')

    def testExisting(self):
        """ pysupport: import name from existing module """
        from MoinMoin.parser import wiki
        Parser = pysupport.importName('MoinMoin.parser.wiki', 'Parser')
        self.failUnless(Parser is wiki.Parser)
   

class ImportNameFromPlugin(unittest.TestCase):
    """ Base class for import plugin tests """
    
    name = 'Parser'
    
    def setUp(self):
        """ Check for valid plugin package """
        self.pluginDirectory = os.path.join(self.request.cfg.data_dir,
                                            'plugin', 'parser')
        self.checkPackage(self.pluginDirectory)
        self.pluginModule = (self.request.cfg.siteid + '.plugin.parser.' +
                             self.plugin)

    def checkPackage(self, path):
        for item in (path, os.path.join(path, '__init__.py')):
            if not os.path.exists(item):
                raise TestSkiped("Missing or wrong permissions: %s" % item)

    def pluginExists(self):
        return (os.path.exists(self.pluginFilePath('.py')) or
                os.path.exists(self.pluginFilePath('.pyc')))

    def pluginFilePath(self, suffix):
        return os.path.join(self.pluginDirectory, self.plugin + suffix)


class ImportNonExisiting(ImportNameFromPlugin):
    
    plugin = 'NonExistingWikiPlugin'

    def testNonEsisting(self):
        """ pysupport: import nonexistent wiki plugin fail """
        if self.pluginExists():
            raise TestSkiped('plugin exists: %s' % self.plugin)
        self.assertRaises(ImportError, pysupport.importName,
                          self.pluginModule, self.name)


class ImportExisting(ImportNameFromPlugin):

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
            raise TestSkiped("Won't overwrite exiting plugin: %s" %
                             self.plugin)
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
            raise TestSkiped("Can't create test plugin: %s" % str(err))
        
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
    
            