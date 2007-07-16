# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.packages tests

    @copyright: 2005 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""


import py

from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.packages import Package, ScriptEngine, MOIN_PACKAGE_FILE, packLine, unpackLine
from MoinMoin._tests.common import gain_superuser_rights


class DebugPackage(Package, ScriptEngine):
    """ Used for debugging, does not need a real .zip file. """
    def __init__(self, request, filename, script=None):
        Package.__init__(self, request)
        ScriptEngine.__init__(self)
        self.filename = filename
        self.script = script or u"""moinmoinpackage|1
print|foo
ReplaceUnderlay|testdatei|TestSeite2
IgnoreExceptions|True
DeletePage|TestSeiteDoesNotExist|Test ...
DeletePage|FooPage|Test ...
IgnoreExceptions|False
AddRevision|foofile|FooPage
AddRevision|foofile|FooPage
setthemename|foo
#foobar
installplugin|foo|local|parser|testy
"""

    def extract_file(self, filename):
        if filename == MOIN_PACKAGE_FILE:
            return self.script.encode("utf-8")
        else:
            return "Hello world, I am the file " + filename.encode("utf-8")

    def filelist(self):
        return [MOIN_PACKAGE_FILE, "foo"]

    def isPackage(self):
        return True


class TestUnsafePackage:
    """ Tests various things in the packages package. Note that this package does
        not care to clean up and needs to run in a test wiki because of that. """

    def setup_class(self):
        if not getattr(self.request.cfg, 'is_test_wiki', False):
            py.test.skip('This test needs to be run using the test wiki.')


    def teardown_class(self):
        DebugPackage(self.request, u"""moinmoinpackage|1
DeletePage|FooPage|Test ...
""").installPackage()


    def testBasicPackageThings(self):
        gain_superuser_rights(self.request)
        myPackage = DebugPackage(self.request, 'test')
        myPackage.installPackage()
        assert myPackage.msg == u'foo\nFooPage added \n'
        testseite2 = Page(self.request, 'TestSeite2')
        assert testseite2.getPageText() == "Hello world, I am the file testdatei"
        assert testseite2.isUnderlayPage()


class TestQuoting:
    def testQuoting(self):
        for line in ([':foo', 'is\\', 'ja|', u't|ü', u'baAzß'], [], ['', '']):
            assert line == unpackLine(packLine(line))

