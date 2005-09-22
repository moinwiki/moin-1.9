# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.util.mail Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin.util import mail

class decodeSpamSafeEmailTestCase(unittest.TestCase):
    """util.mail: testing mail"""
    
    _tests = (
        ('', ''),
        ('AT', '@'),
        ('DOT', '.'),
        ('DASH', '-'),
        ('CAPS', ''),
        ('Mixed', 'Mixed'),
        ('lower', 'lower'),
        ('Firstname DOT Lastname AT example DOT net',
         'Firstname.Lastname@example.net'),
        ('Firstname . Lastname AT exa mp le DOT n e t',
         'Firstname.Lastname@example.net'),
        ('Firstname I DONT WANT SPAM . Lastname@example DOT net',
         'Firstname.Lastname@example.net'),
        ('First name I Lastname DONT AT WANT SPAM example DOT n e t',
         'FirstnameLastname@example.net'),
        ('first.last@example.com', 'first.last@example.com'),
        ('first . last @ example . com', 'first.last@example.com'),
        )

    def testDecodeSpamSafeMail(self):
        """util.mail: decoding spam safe mail"""
        for coded, expected in self._tests:
            result = mail.decodeSpamSafeEmail(coded)
            self.assertEqual(result, expected,
                             'Expected "%(expected)s" but got "%(result)s"' % locals())
