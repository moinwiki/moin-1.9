# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikidicts tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py
import re
import shutil

from MoinMoin import wikidicts
from MoinMoin import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.user import User
from MoinMoin._tests import append_page, become_trusted, create_page, create_random_string_list, nuke_page, nuke_user

class TestGroupPage:

    def testCamelCase(self):
        """ wikidicts: initFromText: CamelCase links """
        text = """
 * CamelCase
"""
        assert self.getMembers(text) == ['CamelCase']

    def testExtendedName(self):
        """ wikidicts: initFromText: extended names """
        text = """
 * extended name
"""
        assert self.getMembers(text) == ['extended name']

    def testExtendedLink(self):
        """ wikidicts: initFromText: extended link """
        text = """
 * [[extended link]]
"""
        assert self.getMembers(text) == ['extended link']

    def testIgnoreSecondLevelList(self):
        """ wikidicts: initFromText: ignore non first level items """
        text = """
  * second level
   * third level
    * forth level
     * and then some...
"""
        assert self.getMembers(text) == []

    def testIgnoreOther(self):
        """ wikidicts: initFromText: ignore anything but first level list itmes """
        text = """
= ignore this =
 * take this

Ignore previous line and this text.
"""
        assert self.getMembers(text) == ['take this']

    def testStripWhitespace(self):
        """ wikidicts: initFromText: strip whitespace around items """
        text = """
 *   take this
"""
        assert self.getMembers(text) == ['take this']

    def getMembers(self, text):
        group = wikidicts.Group(self.request, '')
        group.initFromText(text)
        return group.members()


class TestDictPage:

    def testGroupMembers(self):
        """ wikidicts: create dict from keys and values in text """
        text = '''
Text ignored
 * list items ignored
  * Second level list ignored
 First:: first item
 text with spaces:: second item

Empty lines ignored, so is this text
Next line has key with empty value
 Empty string::\x20
 Last:: last item
'''
        d = wikidicts.Dict(self.request, '')
        d.initFromText(text)
        assert d['First'] == 'first item'
        assert d['text with spaces'] == 'second item'
        assert d['Empty string'] == '' # XXX fails if trailing blank is missing
        assert d['Last'] == 'last item'
        assert len(d) == 4

class TestGroupDicts:

    def testSystemPagesGroupInDicts(self):
        """ wikidict: names in SystemPagesGroup should be in request.dicts

        Get a list of all pages, and check that the dicts list all of them.

        Assume that the SystemPagesGroup is in the data or the underlay dir.
        """
        assert Page.Page(self.request, 'SystemPagesGroup').exists(), "SystemPagesGroup is missing, Can't run test"
        systemPages = wikidicts.Group(self.request, 'SystemPagesGroup')
        #print repr(systemPages)
        #print repr(self.request.dicts['SystemPagesGroup'])
        for member in systemPages.members():
            assert self.request.dicts.has_member('SystemPagesGroup', member), '%s should be in request.dict' % member

        members, groups = self.request.dicts.expand_group('SystemPagesGroup')
        assert 'SystemPagesInEnglishGroup' in groups
        assert 'RecentChanges' in members
        assert 'HelpContents' in members

    def testRenameGroupPage(self):
        """
         tests if the dict cache for groups is refreshed after renaming a Group page
        """
        request = self.request
        become_trusted(request)
        page = create_page(request, u'SomeGroup', u" * ExampleUser")
        page.renamePage('AnotherGroup')
        group = wikidicts.Group(request, '')
        isgroup = request.cfg.cache.page_group_regexact.search
        grouppages = request.rootpage.getPageList(user='', filter=isgroup)
        result = request.dicts.has_member(u'AnotherGroup', u'ExampleUser')
        nuke_page(request, u'AnotherGroup')

        assert result is True

    def testCopyGroupPage(self):
        """
         tests if the dict cache for groups is refreshed after copying a Group page
        """
        request = self.request
        become_trusted(request)
        page = create_page(request, u'SomeGroup', u" * ExampleUser")
        page.copyPage(u'OtherGroup')
        group = wikidicts.Group(request, '')
        isgroup = request.cfg.cache.page_group_regexact.search
        grouppages = request.rootpage.getPageList(user='', filter=isgroup)
        result = request.dicts.has_member(u'OtherGroup', u'ExampleUser')
        nuke_page(request, u'OtherGroup')
        nuke_page(request, u'SomeGroup')

        assert result is True

    def testAppendingGroupPage(self):
        """
         tests scalability by appending a name to a large list of group members
        """
        # long list of users
        page_content = [u" * %s" % member for member in create_random_string_list(length=15, count=30000)]
        request = self.request
        become_trusted(request)
        test_user = create_random_string_list(length=15, count=1)[0]
        page = create_page(request, u'UserGroup', "\n".join(page_content))
        page = append_page(request, u'UserGroup', u' * %s' % test_user)
        result = request.dicts.has_member('UserGroup', test_user)
        nuke_page(request, u'UserGroup')

        assert result is True

    def testUserAppendingGroupPage(self):
        """
         tests appending a username to a large list of group members and user creation
        """
        # long list of users
        page_content = [u" * %s" % member for member in create_random_string_list()]
        request = self.request
        become_trusted(request)
        test_user = create_random_string_list(length=15, count=1)[0]
        page = create_page(request, u'UserGroup', "\n".join(page_content))
        page = append_page(request, u'UserGroup', u' * %s' % test_user)

        # now shortly later we create a user object
        user = User(request, name=test_user)
        if not user.exists():
            User(request, name=test_user, password=test_user).save()

        result = request.dicts.has_member('UserGroup', test_user)
        nuke_page(request, u'UserGroup')
        nuke_user(request, test_user)

        assert result is True

    def testMemberRemovedFromGroupPage(self):
        """
         tests appending a member to a large list of group members and recreating the page without the member
        """
        # long list of users
        page_content = [u" * %s" % member for member in create_random_string_list()]
        page_content = "\n".join(page_content)
        request = self.request
        become_trusted(request)
        test_user = create_random_string_list(length=15, count=1)[0]
        page = create_page(request, u'UserGroup', page_content)
        page = append_page(request, u'UserGroup', u' * %s' % test_user)
        # saves the text without test_user
        page.saveText(page_content, 0)
        result = request.dicts.has_member('UserGroup', test_user)
        nuke_page(request, u'UserGroup')

        assert result is False

    def testGroupPageTrivialChange(self):
        """
         tests appending a username to a group page by trivial change
        """
        request = self.request
        become_trusted(request)
        test_user = create_random_string_list(length=15, count=1)[0]
        member = u" * %s\n" % test_user
        page = create_page(request, u'UserGroup', member)
        # next member saved  as trivial change
        test_user = create_random_string_list(length=15, count=1)[0]
        member = u" * %s\n" % test_user
        page.saveText(member, 0, trivial=1)
        result = request.dicts.has_member('UserGroup', test_user)
        nuke_page(request, u'UserGroup')

        assert result is True

coverage_modules = ['MoinMoin.wikidicts']

