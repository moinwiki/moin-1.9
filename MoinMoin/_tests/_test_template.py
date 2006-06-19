# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.module_tested Tests

    Module names must start with 'test_' to be included in the tests.

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin import module_tested
from MoinMoin._tests import TestConfig


class SimplestTestCase(unittest.TestCase):
    """ The simplest MoinMoin test class

    Class name must ends with 'TestCase' to be included in
    the tests.
    """
    def testSimplest(self):
        """ module_tested: test description... 
        
        Function name MUST start with 'test' to be included in the
        tests. 
        
        The first line of this docstring will show on the test output:
           module_tested: test description ... ok
        """
        # You can access the current request with self.request. It is
        # injected for you into the test class by moin test framework.
        result = module_tested.some_function(self.request, 'test_value')
        expected = 'expected value'
        self.assertEqual(result, expected,
                         ('Expected "%(expected)s" but got "%(result)s"') % locals())
    
    
class ComplexTestCase(unittest.TestCase):
    """ Describe these tests here...

    Some tests may have a list of tests related to this test case. You
    can add a test by adding another line to this list
    """
    _tests = (
        # description,  test,            expected
        ('Line brake',  '[[BR]]',        '<br>'),
    )

    def setUp(self):
        """ Stuff that should run before each test

        Some test needs specific config values, or they will fail.
        """
        self.config = TestConfig(self.request,
                                 defaults=['this option', 'that option'], 
                                 another_option='non default value')
    
    def tearDown(self):
        """ Stuff that should run after each test

        Delete TestConfig, if used.
        """       
        del self.config
    
    def testFunction(self):
        """ module_tested: function should... """
        for description, test, expected in self._tests:
            result = self._helper_function(test)
            self.assertEqual(result, expected,
                             ('%(description)s: expected "%(expected)s" '
                              'but got "%(result)s"') % locals())

    def _helper_fuction(self, test):
        """ Some tests needs extra  work to run

        Keep the test non interesting deatils out of the way.
        """
        module_tested.do_this(self.request)
        module_tested.do_that()

        return result


