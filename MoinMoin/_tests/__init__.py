# -*- coding: iso-8859-1 -*-
"""
MoinMoin Testing Framework
--------------------------

All test modules must be named test_modulename to be included in the
test suit. If you are testing a package, name the test module
test_pakcage_module.

Each test_ module may contain test case classes sub classed from
unittest.TestCase or subclass of it. Previous versions required TestCase
suffix, but now its only a convention.

Each test case class may contain multiply test methods, that must start
with 'test'. Those methods will be run by the test suites.

Test that need the current request, for example to create a page
instance, can refer to self.request. It is injected into all test case
classes by the framework.

Tests that require certain configuration, like section_numbers = 1, must
use a TestConfig to create the required configuration before the
test. Deleting the TestConfig instance will restore the previous
configuration.

See _test_template.py for an example, and use it to create new tests.

Typical Usage
-------------

Running all test in this package::

    from MoinMoin._tests import run
    run(request)

Running only few modules::

    run(request, names=['test_this', 'test_that'])

@copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
@license: GNU GPL, see COPYING for details.
"""

import sys

from unittest import TestLoader, TextTestRunner


class TestSkipped(Exception):
    """ Raised when a tests is skipped """

TestSkiped = TestSkipped # ensure a stable interface

class TestConfig:
    """ Custom configuration for unit tests
    
    Some test assume specific configuration, and will fail if the wiki admin
    will change the configuration. For example, DateTime macro test assume 
    the default datetime_fmt.
    
    When you set custom values in a TestConfig, the previous values are saved,
    and when the TestConfig is deleted, they are restored automatically.
    
    Typical Usage
    -------------
    ::
        from MoinMoin._tests import TestConfig
        class SomeTestCase(unittest.TestCase):
            def setUp(self):
                self.config = TestConfig(self.request,
                                         defaults=key_list, key=value,...)
            def tearDown(self):
                del self.config
            def testSomething(self):
                # test that needs those defaults and custom values
    """

    def __init__(self, request, defaults=(), **custom):
        """ Create temporary configuration for a test 

        @param request: current request
        @param defaults: list of keys that should use the default value
        @param custom: other keys using non default values, or new keys
               that request.cfg does not have already
        """
        self.request = request
        self.old = {}  # Old config values
        self.new = []  # New added attributes
        self.setDefaults(defaults)
        self.setCustom(**custom)

    def setDefaults(self, defaults=()):
        """ Set default values for keys in defaults list
        
        Non existing default will raise an AttributeError.
        """
        from MoinMoin.multiconfig import DefaultConfig
        for key in defaults:
            self._setattr(key, getattr(DefaultConfig, key))

    def setCustom(self, **custom):
        """ Set custom values """
        for key, value in custom.items():
            self._setattr(key, value)

    def _setattr(self, key, value):
        """ Set a new value for key saving new added keys """
        if hasattr(self.request.cfg, key):
            self.old[key] = getattr(self.request.cfg, key)
        else:
            self.new.append(key)
        setattr(self.request.cfg, key, value)

    def __del__(self):
        """ Restore previous request.cfg 
        
        Set old keys to old values and delete new keys.
        """
        for key, value in self.old.items():
            setattr(self.request.cfg, key, value)
        for key in self.new:
            delattr(self.request.cfg, key)


class MoinTestLoader(TestLoader):
    """ Customized test loader that support long running process

    To enable testing long running process, we inject the current
    request into each test case class. Later, each test can refer to
    request as self.request.
    """
    def __init__(self, request):
        self.request = request

    def loadTestsFromTestCase(self, testCaseClass):
        testCaseClass.request = self.request
        return TestLoader.loadTestsFromTestCase(self, testCaseClass)

    def loadTestsFromModuleNames(self, names):
        """ Load tests from qualified module names, eg. a.b.c
        
        loadTestsFromNames is broken, hiding ImportErrros in test
        modules. This method is less flexsible but works correctly.
        """
        names = ['%s.%s' % (__name__, name) for name in names]
        suites = []
        for name in names:
            module = __import__(name, globals(), {}, ['dummy'])
            suites.append(self.loadTestsFromModule(module))
        return self.suiteClass(suites)


def makeSuite(request, names=None):
    """ Create test suites from modules in names

    @param request: current request
    @param names: module names to get tests from. If the list is empty,
        all test modules in the _tests package are used.
    @rtype: C{unittest.TestSuite}
    @return: test suite with all test cases in names
    """
    if not names:
        from MoinMoin.util.pysupport import getPackageModules
        names = getPackageModules(__file__)
        names = [name for name in names if name.startswith('test_')]
        caseInsensitiveCompare = lambda a, b: cmp(a.lower(), b.lower())
        names.sort(caseInsensitiveCompare)

    return MoinTestLoader(request).loadTestsFromModuleNames(names)


def run(request=None, names=None):
    """ Run test suit

    @param request: current request
    @param names: list fully qualified module names to test,
        e.g MoinMoin._tests.test_error
    """
    if request is None:
        from MoinMoin.request import CLI
        from MoinMoin.user import User
        request = CLI.Request()
        request.form = request.args = request.setup_args()
        request.user = User(request)

    suite = makeSuite(request, names)

    # do not redirect the stream to request here because request.write can
    # be invalid or broken because not all redirections of it use a finally: block
    TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)

