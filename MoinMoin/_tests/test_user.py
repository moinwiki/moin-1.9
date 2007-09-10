# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.user Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os
import py

from MoinMoin import user, caching
from MoinMoin.util import filesys


class TestEncodePassword(object):
    """user: encode passwords tests"""

    def testAscii(self):
        """user: encode ascii password"""
        # u'MoinMoin' and 'MoinMoin' should be encoded to same result
        expected = "{SHA}X+lk6KR7JuJEH43YnmettCwICdU="

        result = user.encodePassword("MoinMoin")
        assert result == expected
        result = user.encodePassword(u"MoinMoin")
        assert result == expected

    def testUnicode(self):
        """ user: encode unicode password """
        result = user.encodePassword(u'סיסמה סודית בהחלט') # Hebrew
        expected = "{SHA}GvvkgYzv5MoF9Ljivv2oc81FmkE="
        assert result == expected


class TestLoginWithPassword(object):
    """user: login tests"""

    def setup_method(self, method):
        # Save original user and cookie
        self.saved_cookie = self.request.saved_cookie
        self.saved_user = self.request.user

        # Create anon user for the tests
        self.request.saved_cookie = ''
        self.request.user = user.User(self.request)

        # Prevent user list caching - we create and delete users too fast for that.
        filesys.dcdisable()
        self.user = None

    def teardown_method(self, method):
        """ Run after each test

        Remove user and reset user listing cache.
        """
        # Remove user file and user
        if self.user is not None:
            try:
                path = self.user._User__filename()
                os.remove(path)
            except OSError:
                pass
            del self.user

        # Restore original user
        self.request.saved_cookie = self.saved_cookie
        self.request.user = self.saved_user

        # Remove user name to id cache, or next test will fail
        caching.CacheEntry(self.request, 'user', 'name2id', scope='wiki').remove()
        try:
            del self.request.cfg.cache.name2id
        except:
            pass

        # Prevent user list caching - we create and delete users too fast for that.
        filesys.dcdisable()

    def testAsciiPassword(self):
        """ user: login with ascii password """
        # Create test user
        name = u'__Non Existent User Name__'
        password = name
        self.createUser(name, password)

        # Try to "login"
        theUser = user.User(self.request, name=name, password=password)
        assert theUser.valid

    def testUnicodePassword(self):
        """ user: login with non-ascii password """
        # Create test user
        name = u'__שם משתמש לא קיים__' # Hebrew
        password = name
        self.createUser(name, password)

        # Try to "login"
        theUser = user.User(self.request, name=name, password=password)
        assert theUser.valid

    def testOldNonAsciiPassword(self):
        """ user: login with non-ascii password in pre 1.3 user file

        When trying to login with an old non-ascii password in the user
        file, utf-8 encoded password will not match. In this case, try
        all other encoding available on pre 1.3 before failing.
        """
        # Create test user
        # Use iso charset to create user with old enc_password, as if
        # the user file was migrated from pre 1.3 wiki.
        name = u'__Jürgen Herman__'
        password = name
        self.createUser(name, password, charset='iso-8859-1')

        # Try to "login"
        theUser = user.User(self.request, name=name, password=password)
        assert theUser.valid

    def testReplaceOldNonAsciiPassword(self):
        """ user: login replace old non-ascii password in pre 1.3 user file

        When trying to login with an old non-ascii password in the user
        file, the password hash should be replaced with new utf-8 hash.
        """
        # Create test user
        # Use iso charset to create user with old enc_password, as if
        # the user file was migrated from pre 1.3 wiki.
        name = u'__Jürgen Herman__'
        password = name
        self.createUser(name, password, charset='iso-8859-1')
        # Login - this should replace the old password in the user file
        theUser = user.User(self.request, name=name, password=password)
        # Login again - the password should be new unicode password
        expected = user.encodePassword(password)
        theUser = user.User(self.request, name=name, password=password)
        assert theUser.enc_password == expected

    def testSubscriptionSubscribedPage(self):
        """ user: tests isSubscribedTo  """
        pagename = u'HelpMiscellaneous'
        name = u'__Jürgen Herman__'
        password = name
        self.createUser(name, password, charset='iso-8859-1')
        # Login - this should replace the old password in the user file
        theUser = user.User(self.request, name=name, password=password)
        theUser.subscribe(pagename)
       assert theUser.isSubscribedTo([pagename]) # list(!) of pages to check

    def testSubscriptionSubPage(self):
        """ user: tests isSubscribedTo on a subpage """
        pagename = u'HelpMiscellaneous'
        testPagename = u'HelpMiscellaneous/FrequentlyAskedQuestions'
        name = u'__Jürgen Herman__'
        password = name
        self.createUser(name, password, charset='iso-8859-1')
        # Login - this should replace the old password in the user file
        theUser = user.User(self.request, name=name, password=password)
        theUser.subscribe(pagename)
       assert not theUser.isSubscribedTo([testPagename]) # list(!) of pages to check

    # Helpers ---------------------------------------------------------

    def createUser(self, name, password, charset='utf-8'):
        """ helper to create test user

        charset is used to create user with pre 1.3 password hash
        """
        # Hack self.request form to contain the password
        self.request.form['password'] = [password]

        # Create user
        self.user = user.User(self.request)
        self.user.name = name
        self.user.enc_password = user.encodePassword(password, charset=charset)

        # Validate that we are not modifying existing user data file!
        if self.user.exists():
            self.user = None
            py.test.skip("Test user exists, will not override existing user data file!")

        # Save test user
        self.user.save()

        # Validate user creation
        if not self.user.exists():
            self.user = None
            py.test.skip("Can't create test user")


class TestGroupName(object):

    def setUp(self):
        self.config = self.TestConfig(page_group_regex=r'.+Group')

    def tearDown(self):
        del self.config

    import re
    group = re.compile(r'.+Group', re.UNICODE)

    def testGroupNames(self):
        """ user: isValidName: reject group names """
        test = u'AdminGroup'
        assert self.group.search(test)
        assert not user.isValidName(self.request, test)


class TestIsValidName(object):

    def testNonAlnumCharacters(self):
        """ user: isValidName: reject unicode non alpha numeric characters

        : and , used in acl rules, we might add more characters to the syntax.
        """
        invalid = u'! # $ % ^ & * ( ) = + , : ; " | ~ / \\ \u0000 \u202a'.split()
        base = u'User%sName'
        for c in invalid:
            name = base % c
            assert not user.isValidName(self.request, name)

    def testWhitespace(self):
        """ user: isValidName: reject leading, trailing or multiple whitespace """
        cases = (
            u' User Name',
            u'User Name ',
            u'User   Name',
            )
        for test in cases:
            assert not user.isValidName(self.request, test)

    def testValid(self):
        """ user: isValidName: accept names in any language, with spaces """
        cases = (
            u'Jürgen Hermann', # German
            u'ניר סופר', # Hebrew
            u'CamelCase', # Good old camel case
            u'가각간갇갈 갉갊감 갬갯걀갼' # Hangul (gibberish)
            )
        for test in cases:
            assert user.isValidName(self.request, test)


coverage_modules = ['MoinMoin.user']

