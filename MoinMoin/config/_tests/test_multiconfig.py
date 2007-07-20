# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.config.multiconfig Tests

    @copyright: 2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py


class TestPasswordChecker:
    username = u"SomeUser"
    tests_builtin = [
        (u'', False),
        (u'1966', False),
        (u'asdfghjk', False),
        (u'mnbvcx', False),
        (u'12345678', False),
        (username, False),
        (u'Moin-2007', True),
    ]
    tests_crack = tests_builtin + [
        (u'aaaaaaaa', False),
        (u'secret', False),
        (u'password', False),
    ]
    def testBuiltinPasswordChecker(self):
        pw_checker = self.request.cfg.password_checker
        if not pw_checker:
            py.test.skip("password_checker is disabled in the configuration, not testing it")
        else:
            for pw, result in self.tests_builtin:
                pw_error = pw_checker(self.username, pw)
                print "%r: %s" % (pw, pw_error)
                assert result == (pw_error is None)

    def testCrackPasswordChecker(self):
        pw_checker = self.request.cfg.password_checker
        if not pw_checker:
            py.test.skip("password_checker is disabled in the configuration, not testing it")
        else:
            try:
                import crack # do we have python-crack?
            except:
                py.test.skip("python-crack is not installed")
            try:
                crack.FascistCheck("a12fv./ZX47") # this should not raise an exception
            except:
                py.test.skip("python-crack is not working correctly (did you forget to build the dicts?)")
            else:
                for pw, result in self.tests_crack:
                    pw_error = pw_checker(self.username, pw)
                    print "%r: %s" % (pw, pw_error)
                    assert result == (pw_error is None)


