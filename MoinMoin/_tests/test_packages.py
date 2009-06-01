# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.packages tests

    @copyright: 2005 MoinMoin:AlexanderSchremmer,
                2007 Federico Lorenzi
    @license: GNU GPL, see COPYING for details.
"""

import os
import py
import tempfile
import zipfile

from datetime import datetime
from MoinMoin import user, wikiutil
from MoinMoin.action import AttachFile
from MoinMoin.action.PackagePages import PackagePages
from MoinMoin.packages import Package, ScriptEngine, MOIN_PACKAGE_FILE, ZipPackage, packLine, unpackLine
from MoinMoin._tests import become_superuser, create_page, nuke_page
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor



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
        become_superuser(self.request)
        myPackage = DebugPackage(self.request, 'test')
        myPackage.installPackage()
        assert myPackage.msg == u'foo\nFooPage added \n'
        testseite2 = Page(self.request, 'TestSeite2')
        assert testseite2.getPageText() == "Hello world, I am the file testdatei"
        assert testseite2.isUnderlayPage()


class TestQuoting:

    def testQuoting(self):
        for line in ([':foo', 'is\\', 'ja|', u't|�', u'baAz�'], [], ['', '']):
            assert line == unpackLine(packLine(line))


class TestRealCreation:

    def testSearch(self):
        package = PackagePages(self.request.rootpage.page_name, self.request)
        assert package.searchpackage(self.request, "BadCon") == [u'BadContent']

    def testListCreate(self):
        package = PackagePages(self.request.rootpage.page_name, self.request)
        temp = tempfile.NamedTemporaryFile(suffix='.zip')
        package.collectpackage(['FrontPage'], temp)
        assert zipfile.is_zipfile(temp.name)

    def testAllCreate(self):
        package = PackagePages(self.request.rootpage.page_name, self.request)
        temp = tempfile.NamedTemporaryFile(suffix='.zip')
        package.collectpackage(self.request.rootpage.getPageList(
                                include_underlay=False,
                                filter=lambda name: not wikiutil.isSystemPage(self.request, name)),
                                temp)
        if not package:
            py.test.skip("No user created pages in wiki!")
        assert zipfile.is_zipfile(temp.name)

    def testInvalidCreate(self):
        package = PackagePages(self.request.rootpage.page_name, self.request)
        temp = tempfile.NamedTemporaryFile(suffix='.zip')
        package.collectpackage(['___//THIS PAGE SHOULD NOT EXIST\\___'], temp)
        assert not zipfile.is_zipfile(temp.name)


class TestRealPackageInstallation:


    def create_package(self, script, page=None):
        # creates the package example zip file
        userid = user.getUserIdentification(self.request)
        COMPRESSION_LEVEL = zipfile.ZIP_DEFLATED
        zip_file = tempfile.mkstemp(suffix='.zip')[1]
        zf = zipfile.ZipFile(zip_file, "w", COMPRESSION_LEVEL)
        if page:
            timestamp = wikiutil.version2timestamp(page.mtime_usecs())
            zi = zipfile.ZipInfo(filename="1", date_time=datetime.fromtimestamp(timestamp).timetuple()[:6])
            zi.compress_type = COMPRESSION_LEVEL
            zf.writestr(zi, page.get_raw_body().encode("utf-8"))
        zf.writestr("1_attachment", "sample attachment")
        zf.writestr(MOIN_PACKAGE_FILE, script.encode("utf-8"))
        zf.close()
        return zip_file

    def testAttachments_after_page_creation(self):
        pagename = u'PackageTestPageCreatedFirst'
        page = create_page(self.request, pagename, u"This page has not yet an attachments dir")
        script = u"""MoinMoinPackage|1
AddRevision|1|%(pagename)s
AddAttachment|1_attachment|my_test.txt|%(pagename)s
Print|Thank you for using PackagePages!
""" % {"pagename": pagename}
        zip_file = self.create_package(script, page)
        package = ZipPackage(self.request, zip_file)
        package.installPackage()
        assert Page(self.request, pagename).exists()
        assert AttachFile.exists(self.request, pagename, "my_test.txt")

        nuke_page(self.request, pagename)
        os.unlink(zip_file)

    def testAttachments_without_page_creation(self):
        pagename = u"PackageAttachmentAttachWithoutPageCreation"
        script = u"""MoinMoinPackage|1
AddAttachment|1_attachment|my_test.txt|%(pagename)s
Print|Thank you for using PackagePages!
""" % {"pagename": pagename}
        zip_file = self.create_package(script)
        package = ZipPackage(self.request, zip_file)
        package.installPackage()
        assert not Page(self.request, pagename).exists()
        assert AttachFile.exists(self.request, pagename, "my_test.txt")

        nuke_page(self.request, pagename)
        os.unlink(zip_file)


coverage_modules = ['MoinMoin.packages']

