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
use a Config class to define the required configuration within the test class.

@copyright: 2005 MoinMoin:NirSoffer,
            2007 MoinMoin:AlexanderSchremmer,
            2008 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

import atexit
import sys

import py

rootdir = py.magic.autopath().dirpath()
moindir = rootdir.join("..")
sys.path.insert(0, str(moindir))

from MoinMoin.support.python_compatibility import set
from MoinMoin._tests import maketestwiki, wikiconfig

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
        module_list = [sys.modules[mod] for mod in coverage_modules]
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


def init_test_request(given_config=None, static_state=[False]):
    from MoinMoin.request import request_cli
    from MoinMoin.user import User
    from MoinMoin.formatter.text_html import Formatter as HtmlFormatter
    if not static_state[0]:
        maketestwiki.run(True)
        static_state[0] = True
    request = request_cli.Request(given_config=given_config)
    request.form = request.args = request.setup_args()
    request.user = User(request)
    request.html_formatter = HtmlFormatter(request)
    request.formatter = request.html_formatter
    return request


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
        if hasattr(cls, 'Config'):
            cls.request = init_test_request(given_config=cls.Config)
        else:
            cls.request = self.parent.request
        super(MoinClassCollector, self).setup()


class Module(py.test.collect.Module):
    Class = MoinClassCollector
    Function = MoinTestFunction

    def __init__(self, *args, **kwargs):
        self.request = init_test_request(given_config=wikiconfig.Config)
        super(Module, self).__init__(*args, **kwargs)

    def run(self, *args, **kwargs):
        if coverage is not None:
            coverage_modules.update(getattr(self.obj, 'coverage_modules', []))
        return super(Module, self).run(*args, **kwargs)

