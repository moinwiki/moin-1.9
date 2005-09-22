# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.scripts.repair_language tests

    @copyright: 2003-2004 by Nir Soffer <nirs@freeshell.org>
    @license: GNU GPL, see COPYING for details.
"""

import unittest

from MoinMoin.scripts.repair_language import repairText


class RepairTestCase(unittest.TestCase):

    def testPageContent(self):
        ''' repair_language: should not replace in page body '''
        text = 'Should not replace in page content'
        self.assertEqual((text, 0), repairText(text))

    def testUnknwonLanguage(self):
        ''' repair_language: should not replace unknown langauge '''
        text = '##language:ar'
        self.assertEqual((text, 0), repairText(text))
    
    def testKnownLanguage(self):
        """ repair_language: should replace known language """
        before = u'##language:en\r\n'
        after = u'#language en\r\n'
        self.assertEqual((after, 1), repairText(before))

    def testLineEndings(self):
        """ repair_language: return crlf line endings """
        before = (u'##language:en\r\n'
                  u'page content\r\n')
        after = (u'#language en\r\n'
                 u'page content\r\n')
        self.assertEqual((after, 1), repairText(before))
        
