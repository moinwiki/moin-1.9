# -*- coding: iso-8859-1 -*-
"""
MoinMoin - MoinMoin.backends.wiki_group tests

@copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
            2007 by MoinMoin:ThomasWaldmann
            2008 by MoinMoin:MelitaMihaljevic
            2009 by MoinMoin:DmitrijsMilajevs
@license: GNU GPL, see COPYING for details.
"""

from py.test import raises
import re, shutil

from MoinMoin.datastruct.backends._tests import GroupsBackendTest
from MoinMoin.datastruct import WikiGroups
from MoinMoin import Page, security
from MoinMoin.PageEditor import PageEditor
from MoinMoin.user import User
from MoinMoin._tests import append_page, become_trusted, create_page, create_random_string_list, nuke_page, nuke_user, wikiconfig


class TestWikiGroupBackend(GroupsBackendTest):

    # Suppose that default configuration for the groups is used which
    # is WikiGroups backend.

    def setup_class(self):
        become_trusted(self.request)

        for group, members in self.test_groups.iteritems():
            page_text = ' * %s' % '\n * '.join(members)
            create_page(self.request, group, page_text)

    def teardown_class(self):
        become_trusted(self.request)

        for group in self.test_groups:
            nuke_page(self.request, group)

    def test_rename_group_page(self):
        """
        Tests if the groups cache is refreshed after renaming a Group page.
        """
        request = self.request
        become_trusted(request)

        page = create_page(request, u'SomeGroup', u" * ExampleUser")
        page.renamePage('AnotherGroup')

        result = u'ExampleUser' in request.groups[u'AnotherGroup']
        nuke_page(request, u'AnotherGroup')

        assert result is True

    def test_copy_group_page(self):
        """
        Tests if the groups cache is refreshed after copying a Group page.
        """
        request = self.request
        become_trusted(request)

        page = create_page(request, u'SomeGroup', u" * ExampleUser")
        page.copyPage(u'SomeOtherGroup')

        result = u'ExampleUser' in request.groups[u'SomeOtherGroup']

        nuke_page(request, u'OtherGroup')
        nuke_page(request, u'SomeGroup')

        assert result is True

    def test_appending_group_page(self):
        """
        Test scalability by appending a name to a large list of group members.
        """
        request = self.request
        become_trusted(request)

        # long list of users
        page_content = [u" * %s" % member for member in create_random_string_list(length=15, count=1234)]
        test_user = create_random_string_list(length=15, count=1)[0]
        create_page(request, u'UserGroup', "\n".join(page_content))
        append_page(request, u'UserGroup', u' * %s' % test_user)
        result = test_user in request.groups['UserGroup']
        nuke_page(request, u'UserGroup')

        assert result

    def test_user_addition_to_group_page(self):
        """
        Test addition of a username to a large list of group members.
        """
        request = self.request
        become_trusted(request)

        # long list of users
        page_content = [u" * %s" % member for member in create_random_string_list()]
        create_page(request, u'UserGroup', "\n".join(page_content))

        new_user = create_random_string_list(length=15, count=1)[0]
        append_page(request, u'UserGroup', u' * %s' % new_user)
        user = User(request, name=new_user)
        if not user.exists():
            User(request, name=new_user, password=new_user).save()

        result = new_user in request.groups[u'UserGroup']
        nuke_page(request, u'UserGroup')
        nuke_user(request, new_user)

        assert result

    def test_member_removed_from_group_page(self):
        """
        Tests appending a member to a large list of group members and
        recreating the page without the member.
        """
        request = self.request
        become_trusted(request)

        # long list of users
        page_content = [u" * %s" % member for member in create_random_string_list()]
        page_content = "\n".join(page_content)
        create_page(request, u'UserGroup', page_content)

        test_user = create_random_string_list(length=15, count=1)[0]
        page = append_page(request, u'UserGroup', u' * %s' % test_user)

        # saves the text without test_user
        page.saveText(page_content, 0)
        result = test_user in request.groups[u'UserGroup']
        nuke_page(request, u'UserGroup')

        assert not result

    def test_group_page_user_addition_trivial_change(self):
        """
        Test addition of a user to a group page by trivial change.
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

        assert result

    def test_wiki_backend_page_acl_append_page(self):
        """
        Test if the wiki group backend works with acl code.
        First check acl rights of a user that is not a member of group
        then add user member to a page group and check acl rights
        """
        request = self.request
        become_trusted(request)

        create_page(request, u'NewGroup', u" * ExampleUser")

        acl_rights = ["NewGroup:read,write"]
        acl = security.AccessControlList(request.cfg, acl_rights)

        has_rights_before = acl.may(request, u"AnotherUser", "read")

        # update page - add AnotherUser to a page group NewGroup
        append_page(request, u'NewGroup', u" * AnotherUser")

        has_rights_after = acl.may(request, u"AnotherUser", "read")

        nuke_page(request, u'NewGroup')

        assert not has_rights_before, 'AnotherUser has no read rights because in the beginning he is not a member of a group page NewGroup'
        assert has_rights_after, 'AnotherUser must have read rights because after appendage he is member of NewGroup'

    def test_simple_group_page(self):
        """
        Tests if a simple group page is evaluated correctly.
        """
        request = self.request
        become_trusted(request)
        group_name = u'SimpleGroup'
        page_text = u"""\
 * FirstUser
 * SecondUser
 * LastUser"""
        page = create_page(request, group_name, page_text)
        group_members = set(request.groups[group_name])
        assert group_members == set([u'FirstUser', u'SecondUser', u'LastUser'])
        nuke_page(request, group_name)

    def test_complex_group_page(self):
        """
        Tests if a complex group page is evaluated correctly.
        """
        request = self.request
        become_trusted(request)
        group_name = u'ComplexGroup'
        page_text = u"""\
 * FirstUser
  * any text
 * SecondUser
 * LastUser
  * any text"""
        page = create_page(request, group_name, page_text)
        group_members = set(request.groups[group_name])
        assert group_members == set([u'FirstUser', u'SecondUser', u'LastUser'])
        nuke_page(request, group_name)

coverage_modules = ['MoinMoin.datastruct.backends.wiki_groups']

