# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.config.multiconfig Tests

    @copyright: 2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py
from MoinMoin.support.python_compatibility import set


class TestPasswordChecker:
    username = u"SomeUser"
    tests_builtin = [
        (u'', False), # empty
        (u'1966', False), # too short
        (u'asdfghjk', False), # keyboard sequence
        (u'QwertZuiop', False), # german keyboard sequence, with uppercase
        (u'mnbvcx', False), # reverse keyboard sequence
        (u'12345678', False), # keyboard sequence, too easy
        (u'aaaaaaaa', False), # not enough different chars
        (u'BBBaaaddd', False), # not enough different chars
        (username, False), # username == password
        (username[1:-1], False), # password in username
        (u"XXX%sXXX" % username, False), # username in password
        (u'Moin-2007', True), # this should be OK
    ]
    def testBuiltinPasswordChecker(self):
        pw_checker = self.request.cfg.password_checker
        if not pw_checker:
            py.test.skip("password_checker is disabled in the configuration, not testing it")
        else:
            for pw, result in self.tests_builtin:
                pw_error = pw_checker(self.request, self.username, pw)
                print "%r: %s" % (pw, pw_error)
                assert result == (pw_error is None)

coverage_modules = ['MoinMoin.config.multiconfig']

