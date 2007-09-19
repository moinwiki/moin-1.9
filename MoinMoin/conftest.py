# -*- coding: iso-8859-1 -*-
"""
MoinMoin Testing Framework
--------------------------

All test modules must be named test_modulename to be included in the
test suite. If you are testing a package, name the test module
test_package_module.

Tests that need the current request, for example to create a page
instance, can refer to self.request. It is injected into all test case
classes by the framework.

Tests that require a certain configuration, like section_numbers = 1, must
use a TestConfig to create the required configuration before the test.
Deleting the TestConfig instance will restore the previous configuration.

@copyright: 2005 Nir Soffer, 2007 Alexander Schremmer
@license: GNU GPL, see COPYING for details.
"""

import atexit
from inspect import isclass
from sys import modules
import sys

import py


rootdir = py.magic.autopath().dirpath()
moindir = rootdir.join("..")

sys.path.insert(0, str(moindir))
from MoinMoin._tests import maketestwiki, compat
modules["unittest"] = compat # evil hack

sys.path.insert(0, str(moindir.join("tests")))

from MoinMoin.support.python_compatibility import set

coverage_modules = set()


try:
    """
    This code adds support for coverage.py (see
    http://nedbatchelder.com/code/modules/coverage.html).
    It prints a coverage report for the modules specified in all
    module globals (of the test modules) named "coverage_modules".
    """

    import coverage

    def report_coverage():
        coverage.stop()
        module_list = [modules[mod] for mod in coverage_modules]
        module_list.sort()
        coverage.report(module_list)

    def callback(option, opt_str, value, parser):
        atexit.register(report_coverage)
        coverage.erase()
        coverage.start()


    py.test.config.addoptions('MoinMoin options', py.test.config.Option('-C',
        '--coverage', action='callback', callback=callback,
        help='Output information about code coverage (slow!)'))

except ImportError:
    coverage = None


def init_test_request(static_state=[False]):
    from MoinMoin.request import request_cli
    from MoinMoin.user import User
    from MoinMoin.formatter.text_html import Formatter as HtmlFormatter
    if not static_state[0]:
        maketestwiki.run(True)
        static_state[0] = True
    request = request_cli.Request()
    request.form = request.args = request.setup_args()
    request.user = User(request)
    request.html_formatter = HtmlFormatter(request)
    request.formatter = request.html_formatter
    return request


class TestConfig:
    """ Custom configuration for unit tests

    Some tests assume a specific configuration, and will fail if the wiki admin
    changed the configuration. For example, DateTime macro test assume
    the default datetime_fmt.

    When you set custom values in a TestConfig, the previous values are saved,
    and when the TestConfig is called specifically, they are restored automatically.

    Typical Usage
    -------------
    ::
        class SomeTest:
            def setUp(self):
                self.config = self.TestConfig(defaults=key_list, key=value,...)
            def tearDown(self):
                self.config.restore()
            def testSomething(self):
                # test that needs those defaults and custom values
    """

    def __init__(self, request):
        """ Create temporary configuration for a test

        @param request: current request
        """
        self.request = request
        self.old = {}  # Old config values
        self.new = []  # New added attributes

    def __call__(self, defaults=(), **custom):
        """ Initialise a temporary configuration for a test

        @param defaults: list of keys that should use the default value
        @param custom: other keys using non default values, or new keys
               that request.cfg does not have already
        """
        self.setDefaults(defaults)
        self.setCustom(**custom)

        return self

    def setDefaults(self, defaults=()):
        """ Set default values for keys in defaults list

        Non existing default will raise an AttributeError.
        """
        from MoinMoin.config import multiconfig
        for key in defaults:
            self._setattr(key, getattr(multiconfig.DefaultConfig, key))

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

    def restore(self):
        """ Restore previous request.cfg

        Set old keys to old values and delete new keys.
        """
        for key, value in self.old.items():
            setattr(self.request.cfg, key, value)
        for key in self.new:
            delattr(self.request.cfg, key)
    __del__ = restore # XXX __del__ semantics are currently broken



# py.test customization starts here

class MoinTestFunction(py.test.collect.Function):
    def execute(self, target, *args):
        request = self.parent.request
        co = target.func_code
        if 'request' in co.co_varnames[:co.co_argcount]:
            target(request, *args)
        else:
            target(*args)


class MoinClassCollector(py.test.collect.Class):
    Function = MoinTestFunction

    def setup(self):
        cls = self.obj
        cls.request = self.parent.request
        cls.TestConfig = TestConfig(cls.request)
        super(MoinClassCollector, self).setup()


class Module(py.test.collect.Module):
    Class = MoinClassCollector
    Function = MoinTestFunction

    def __init__(self, *args, **kwargs):
        self.request = init_test_request()
        super(Module, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        if coverage is not None:
            coverage_modules.update(getattr(self.obj, 'coverage_modules', []))
        return super(Module, self).run(*args, **kwargs)

