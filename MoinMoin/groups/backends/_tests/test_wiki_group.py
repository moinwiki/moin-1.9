# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikidicts tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.

"""

import py
import re
import shutil

from py.test import raises

from MoinMoin.groups.backends import wiki_group
from MoinMoin import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.user import User
from MoinMoin._tests import append_page, become_trusted, create_page, create_random_string_list, nuke_page, nuke_user, wikiconfig
from MoinMoin.groups import GroupManager

class TestWikiGroupPage:
    """
    Test what backend extracts from a group page and what is ignored.
    """

    class Config(wikiconfig.Config):
        def group_manager_init(self, request):
            return GroupManager(backends=[wiki_group.Backend(request)])

    def testCamelCase(self):
        text = """
 * CamelCase
"""
        assert u'CamelCase' in self.getGroup(text)

    def testExtendedName(self):
        text = """
 * extended name
"""
        assert u'extended name' in self.getGroup(text)

    def testExtendedLink(self):
        text = """
 * [[extended link]]
"""
        assert u'extended link' in self.getGroup(text)

    def testIgnoreSecondLevelList(self):
        text = """
  * second level
   * third level
    * forth level
     * and then some...
"""
        assert len([x for x in self.getGroup(text)]) == 0

    def testIgnoreOther(self):
        text = """
= ignore this =
 * take this

Ignore previous line and this text.
"""
        assert u'take this' in self.getGroup(text)

    def testStripWhitespace(self):
        text = """
 *   take this
"""
        assert u'take this' in self.getGroup(text)

    def getGroup(self, text):
        request = self.request
        become_trusted(request)
        create_page(request, u'SomeTestGroup', text)
        group = request.groups[u'SomeTestGroup']
        nuke_page(request, u'SomeTestGroup')
        return group


class TestWikiGroupBackend:

    class Config(wikiconfig.Config):
        def group_manager_init(self, request):
            return GroupManager(backends=[wiki_group.Backend(request)])

    def setup_method(self, method):

        become_trusted(self.request)

        self.wiki_group_page_name = u'TestWikiGroup'
        wiki_group_page_text = u"""
 * Apple
 * Banana
 * OtherGroup"""
        create_page(self.request, self.wiki_group_page_name, wiki_group_page_text)

        self.other_group_page_name = u'OtherGroup'
        other_group_page_text = u"""
 * Admin
 * Editor
 * Apple"""
        create_page(self.request, self.other_group_page_name, other_group_page_text)

        self.third_group_page_name = u'ThirdGroup'
        third_group_page_text = u' * Other'
        create_page(self.request, self.third_group_page_name, third_group_page_text)

    def teardown_method(self, method):
        become_trusted(self.request)
        nuke_page(self.request, self.wiki_group_page_name)
        nuke_page(self.request, self.other_group_page_name)
        nuke_page(self.request, self.third_group_page_name)

    def testContainment(self):
        groups = self.request.groups

        assert u'Banana' in groups[u'TestWikiGroup']
        assert u'Apple' in groups[u'TestWikiGroup']

        assert u'Apple' in groups[u'OtherGroup']
        assert u'Admin' in groups[u'OtherGroup']

        apple_groups = groups.membergroups(u'Apple')
        assert 2 == len(apple_groups), 'Groups must be automatically expanded'
        assert u'TestWikiGroup' in apple_groups
        assert u'OtherGroup' in apple_groups
        assert u'ThirdGroup' not in apple_groups

        raises(KeyError, lambda: groups[u'NotExistingssssGroup'])

        assert u'ThirdGroup' in groups

    def testRenameGroupPage(self):
        """
         tests if the dict cache for groups is refreshed after
         renaming a Group page
        """
        request = self.request
        become_trusted(request)

        page = create_page(request, u'SomeGroup', u" * ExampleUser")
        page.renamePage('AnotherGroup')

        result = u'ExampleUser' in request.groups[u'AnotherGroup']
        nuke_page(request, u'AnotherGroup')

        assert result is True

    def testCopyGroupPage(self):
        """
         tests if the dict cache for groups is refreshed after copying a Group page
        """
        request = self.request
        become_trusted(request)

        page = create_page(request, u'SomeGroup', u" * ExampleUser")
        page.copyPage(u'SomeOtherGroup')

        result = u'ExampleUser' in request.groups[u'SomeOtherGroup']

        nuke_page(request, u'OtherGroup')
        nuke_page(request, u'SomeGroup')

        assert result is True

    def testAppendingGroupPage(self):
        """
         tests scalability by appending a name to a large list of
         group members
        """
        # long list of users
        page_content = [u" * %s" % member for member in create_random_string_list(length=15, count=30000)]
        request = self.request
        become_trusted(request)
        test_user = create_random_string_list(length=15, count=1)[0]
        page = create_page(request, u'UserGroup', "\n".join(page_content))
        page = append_page(request, u'UserGroup', u' * %s' % test_user)
        result = test_user in request.groups['UserGroup']
        nuke_page(request, u'UserGroup')

        assert result is True

    def testUserAppendingGroupPage(self):
        """
         tests appending a username to a large list of group members
         and user creation
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

        result = test_user in request.groups[u'UserGroup']
        nuke_page(request, u'UserGroup')
        nuke_user(request, test_user)

        assert result is True

    def testMemberRemovedFromGroupPage(self):
        """
         tests appending a member to a large list of group members and
         recreating the page without the member
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
        result = test_user in request.groups[u'UserGroup']
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
        result = test_user in request.groups[u'UserGroup']
        nuke_page(request, u'UserGroup')

        assert result is True


coverage_modules = ['MoinMoin.groups.backends.wiki_group']

