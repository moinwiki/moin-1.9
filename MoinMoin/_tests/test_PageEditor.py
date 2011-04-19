# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.PageEditor Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin import wikiutil
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.security import parseACL

# TODO: check if and where we can use the helpers:
from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestExpandVars(object):
    """PageEditor: testing page editor"""
    pagename = u'AutoCreatedMoinMoinTemporaryTestPage'

    _tests = (
        # Variable,             Expanded
        ("@PAGE@", pagename),
        ("em@PAGE@bedded", "em%sbedded" % pagename),
        ("@NOVAR@", "@NOVAR@"),
        ("case@Page@sensitive", "case@Page@sensitive"),
        )

    def setup_method(self, method):
        self.page = PageEditor(self.request, self.pagename)

    def testExpandVariables(self):
        """ PageEditor: expand general variables """
        for var, expected in self._tests:
            result = self.page._expand_variables(var)
            assert result == expected


class TestExpandUserName(object):
    """ Base class for user name tests

    Set user name during tests.
    """
    pagename = u'AutoCreatedMoinMoinTemporaryTestPage'
    variable = u'@USERNAME@'

    def setup_method(self, method):
        self.page = PageEditor(self.request, self.pagename)
        self.savedName = self.request.user.name
        self.request.user.name = self.name

    def teardown_method(self, method):
        self.request.user.name = self.savedName

    def expand(self):
        return self.page._expand_variables(self.variable)


class TestExpandCamelCaseName(TestExpandUserName):

    name = u'UserName'

    def testExpandCamelCaseUserName(self):
        """ PageEditor: expand @USERNAME@ CamelCase """
        assert self.expand() == self.name


class TestExpandExtendedName(TestExpandUserName):

    name = u'user name'

    def testExtendedNamesEnabled(self):
        """ PageEditor: expand @USERNAME@ extended name - enabled """
        assert self.expand() == u'[[%s]]' % self.name


class TestExpandMailto(TestExpandUserName):

    variable = u'@MAILTO@'
    name = u'user name'
    email = 'user@example.com'

    def setup_method(self, method):
        super(TestExpandMailto, self).setup_method(method)
        self.savedValid = self.request.user.valid
        self.request.user.valid = 1
        self.savedEmail = self.request.user.email
        self.request.user.email = self.email

    def teardown_method(self, method):
        super(TestExpandMailto, self).teardown_method(method)
        self.request.user.valid = self.savedValid
        self.request.user.email = self.savedEmail

    def testMailto(self):
        """ PageEditor: expand @MAILTO@ """
        assert self.expand() == u'<<MailTo(%s)>>' % self.email


class TestExpandPrivateVariables(TestExpandUserName):

    variable = u'@ME@'
    name = u'AutoCreatedMoinMoinTemporaryTestUser'
    dictPage = name + '/MyDict'
    shouldDeleteTestPage = True

    def setup_method(self, method):
        super(TestExpandPrivateVariables, self).setup_method(method)
        self.savedValid = self.request.user.valid
        self.request.user.valid = 1
        self.createTestPage()
        self.deleteCaches()

    def teardown_method(self, method):
        super(TestExpandPrivateVariables, self).teardown_method(method)
        self.request.user.valid = self.savedValid
        self.deleteTestPage()

    def testPrivateVariables(self):
        """ PageEditor: expand user variables """
        assert self.expand() == self.name

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
        # New dicts does not require cache refresh.

    def deleteTestPage(self):
        """ Delete temporary page, bypass logs and notifications """
        if self.shouldDeleteTestPage:
            import shutil
            shutil.rmtree(self.dictPagePath(), True)

    def dictPagePath(self):
        page = Page(self.request, self.dictPage)
        return page.getPagePath(use_underlay=0, check_create=0)


class TestSave(object):

    def setup_method(self, method):
        self.old_handlers = self.request.cfg.event_handlers
        become_trusted(self.request)

    def teardown_method(self, method):
        self.request.cfg.event_handlers = self.old_handlers
        nuke_page(self.request, u'AutoCreatedMoinMoinTemporaryTestPageFortestSave')

    def testSaveAbort(self):
        """Test if saveText() is interrupted if PagePreSave event handler returns Abort"""

        def handler(event):
            from MoinMoin.events import Abort
            return Abort("This is just a test")

        pagename = u'AutoCreatedMoinMoinTemporaryTestPageFortestSave'
        testtext = u'ThisIsSomeStupidTestPageText!'

        self.request.cfg.event_handlers = [handler]

        page = Page(self.request, pagename)
        if page.exists():
            deleter = PageEditor(self.request, pagename)
            deleter.deletePage()

        editor = PageEditor(self.request, pagename)
        editor.saveText(testtext, 0)

        print "PageEditor can't save a page if Abort is returned from PreSave event handlers"
        page = Page(self.request, pagename)
        assert page.body != testtext


class TestSaveACLChange(object):
    from MoinMoin._tests import wikiconfig
    class Config(wikiconfig.Config):
        acl_rights_before = 'Trusted:read,write,delete,revert'
        acl_rights_default = 'All:read,write'

    pagename = u'PageACLTest'
    oldtext = u'''\
## foo
#lang en

foo
'''
    newtext = u'''\
## foo
#acl -All:write Default
#lang en

foo
'''

    def setup_method(self, method):
        p = PageEditor(self.request, self.pagename)
        p.saveText(self.oldtext, 0)

    def teardown_method(self, method):
        become_trusted(self.request)
        nuke_page(self.request, self.pagename)

    def test_acls(self):
        p = PageEditor(self.request, self.pagename)
        oldacl = p.getACL(self.request).acl
        assert not self.request.user.may.admin(p.page_name)
        newacl = parseACL(self.request, self.newtext).acl
        assert newacl != oldacl
        py.test.raises(PageEditor.NoAdmin, p.saveText, self.newtext, 0)


class TestDictPageDeletion(object):

    def testCreateDictAndDeleteDictPage(self):
        """
        simple test if it is possible to delete a Dict page after creation
        """
        become_trusted(self.request)
        pagename = u'SomeDict'
        page = PageEditor(self.request, pagename, do_editor_backup=0)
        body = u"This is an example text"
        page.saveText(body, 0)

        success_i, result = page.deletePage()

        expected = u'Page "SomeDict" was successfully deleted!'

        assert result == expected

class TestCopyPage(object):

    pagename = u'AutoCreatedMoinMoinTemporaryTestPage'
    copy_pagename = u'AutoCreatedMoinMoinTemporaryCopyTestPage'
    shouldDeleteTestPage = True
    text = u'Example'

    def setup_method(self, method):
        self.savedValid = self.request.user.valid
        self.request.user.valid = 1

    def teardown_method(self, method):
        self.request.user.valid = self.savedValid
        self.deleteTestPage()

    def createTestPage(self):
        """ Create temporary page, bypass logs, notification and backups

        TODO: this code is very fragile, any change in the
        implementation will break this test. Need to factor PageEditor
        to make it possible to create page without loging and notifying.
        """
        import os
        path = Page(self.request, self.pagename).getPagePath(check_create=0)
        copy_path = Page(self.request, self.copy_pagename).getPagePath(check_create=0)

        if os.path.exists(path) or os.path.exists(copy_path):
            self.shouldDeleteTestPage = False
            py.test.skip("%s or %s exists. Won't overwrite exiting page" % (self.pagename, self.copy_pagename))
        try:
            os.mkdir(path)
            revisionsDir = os.path.join(path, 'revisions')
            os.mkdir(revisionsDir)
            current = '00000001'
            file(os.path.join(path, 'current'), 'w').write('%s\n' % current)

            file(os.path.join(revisionsDir, current), 'w').write(self.text)
        except Exception, err:
            py.test.skip("Can not be create test page: %s" % err)

    def deleteTestPage(self):
        """ Delete temporary page, bypass logs and notifications """
        if self.shouldDeleteTestPage:
            import shutil
            shutil.rmtree(Page(self.request, self.pagename).getPagePath(), True)
            shutil.rmtree(Page(self.request, self.copy_pagename).getPagePath(), True)

    def test_copy_page(self):
        """
        Tests copying a page without restricted acls
        """
        self.createTestPage()
        result, msg = PageEditor(self.request, self.pagename).copyPage(self.copy_pagename)
        revision = Page(self.request, self.copy_pagename).current_rev()
        assert result and revision is 2

    def test_copy_page_acl_read(self):
        """
        Tests copying a page without write rights
        """
        self.text = u'#acl SomeUser:read,write,delete All:read\n'
        self.createTestPage()
        result, msg = PageEditor(self.request, self.pagename).copyPage(self.copy_pagename)
        revision = Page(self.request, self.copy_pagename).current_rev()
        assert result and revision is 2

    def test_copy_page_acl_no_read(self):
        """
        Tests copying a page without read rights
        """
        self.text = u'#acl SomeUser:read,write,delete All:\n'
        self.createTestPage()
        result, msg = PageEditor(self.request, self.pagename).copyPage(self.copy_pagename)
        revision = Page(self.request, self.copy_pagename).current_rev()
        assert result and revision is 2

coverage_modules = ['MoinMoin.PageEditor']
