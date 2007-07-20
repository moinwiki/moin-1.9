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
    tests_crack = tests_builtin + [
        (u'secret', False), # word from dictionary
        (u'password', False), # word from dictionary
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


