# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.mail.sendmail Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from email.Charset import Charset, QP
from email.Header import Header
from MoinMoin.mail import sendmail
from MoinMoin import config


class decodeSpamSafeEmailTestCase(unittest.TestCase):
    """mail.sendmail: testing mail"""

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
        """mail.sendmail: decoding spam safe mail"""
        for coded, expected in self._tests:
            result = sendmail.decodeSpamSafeEmail(coded)
            self.assertEqual(result, expected,
                             'Expected "%(expected)s" but got "%(result)s"' %
                             locals())


class EncodeAddressTests(unittest.TestCase):
    """ Address encoding tests
    
    See http://www.faqs.org/rfcs/rfc2822.html section 3.4. 
    Address Specification.
            
    mailbox     =   name-addr / addr-spec
    name-addr   =   [display-name] angle-addr
    angle-addr  =   [CFWS] "<" addr-spec ">" [CFWS] / obs-angle-addr
    """
    charset = Charset(config.charset)
    charset.header_encoding = QP
    charset.body_encoding = QP

    def testSimpleAddress(self):
        """ mail.sendmail: encode simple address: local@domain """
        address = u'local@domain'
        expected = address.encode(config.charset)
        self.failUnlessEqual(sendmail.encodeAddress(address, self.charset),
                             expected)

    def testComposite(self):
        """ mail.sendmail: encode address: 'Phrase <local@domain>' """
        address = u'Phrase <local@domain>'
        phrase = str(Header(u'Phrase '.encode('utf-8'), self.charset))
        expected = phrase + '<local@domain>'
        self.failUnlessEqual(sendmail.encodeAddress(address, self.charset),
                             expected)

    def testCompositeUnicode(self):
        """ mail.sendmail: encode Uncode address: 'ויקי <local@domain>' """
        address = u'ויקי <local@domain>'
        phrase = str(Header(u'ויקי '.encode('utf-8'), self.charset))
        expected = phrase + '<local@domain>'
        self.failUnlessEqual(sendmail.encodeAddress(address, self.charset),
                             expected)

    def testEmptyPhrase(self):
        """ mail.sendmail: encode address with empty phrase: '<local@domain>' """
        address = u'<local@domain>'
        expected = address.encode(config.charset)
        self.failUnlessEqual(sendmail.encodeAddress(address, self.charset),
                             expected)

    def testEmptyAddress(self):
        """ mail.sendmail: encode address with empty address: 'Phrase <>' 
        
        Let the smtp server handle this. We may raise error in such
        case, but we don't do error checking for mail addresses.
        """
        address = u'Phrase <>'
        phrase = str(Header(u'Phrase '.encode('utf-8'), self.charset))
        expected = phrase + '<>'
        self.failUnlessEqual(sendmail.encodeAddress(address, self.charset),
                             expected)

    def testInvalidAddress(self):
        """ mail.sendmail: encode invalid address 'Phrase <blah' 
        
        Assume that this is a simple address. This address will
        probably cause an error when trying to send mail. Junk in, junk
        out.
        """
        address = u'Phrase <blah'
        expected = address.encode(config.charset)
        self.failUnlessEqual(sendmail.encodeAddress(address, self.charset),
                             expected)

