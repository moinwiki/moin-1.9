# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikidicts tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
import re

from MoinMoin import wikidicts 
from MoinMoin import Page

class GroupPageTestCase(unittest.TestCase):

    def testCamelCase(self):
        """ wikidicts: initFromText: CamelCase links """
        text = """
 * CamelCase
"""
        self.assertEqual(self.getMembers(text), ['CamelCase'])

    def testExtendedName(self):
        """ wikidicts: initFromText: extended names """
        text = """
 * extended name
"""
        self.assertEqual(self.getMembers(text), ['extended name'])

    def testExtendedLink(self):
        """ wikidicts: initFromText: extended link """
        text = """
 * ["extended link"]
"""
        self.assertEqual(self.getMembers(text), ['extended link'])

    def testIgnoreSecondLevelList(self):
        """ wikidicts: initFromText: ignore non first level items """
        text = """
  * second level
   * third level
    * forth level
     * and then some...
"""
        self.assertEqual(self.getMembers(text), [])

    def testIgnoreOther(self):
        """ wikidicts: initFromText: ignore anything but first level list itmes """
        text = """
= ignore this =
 * take this

Ignore previous line and this text.
"""
        self.assertEqual(self.getMembers(text), ['take this'])

    def testStripWhitespace(self):
        """ wikidicts: initFromText: strip whitespace around items """
        text = """
 *   take this  
"""
        self.assertEqual(self.getMembers(text), ['take this'])
        
    def getMembers(self, text):
        group = wikidicts.Group(self.request, '')
        group.initFromText(text)
        return group.members()
        

class DictPageTestCase(unittest.TestCase):

    def testGroupMembers(self):
        """ wikidicts: create dict from keys and values in text """
        text = '''
Text ignored
 * list items ignored
  * Second level list ignored
 First:: first item
 text with spaces:: second item

Empty lines ignored, so is this text
Next line has key with empty value
 Empty string:: 
 Last:: last item
'''
        d = wikidicts.Dict(self.request, '')
        d.initFromText(text)        
        self.assertEqual(d['First'], 'first item')
        self.assertEqual(d['text with spaces'], 'second item')
        self.assertEqual(d['Empty string'], '')        
        self.assertEqual(d['Last'], 'last item')


class GroupDictTestCase(unittest.TestCase):

    def testSystemPagesGroupInDicts(self):
        """ wikidict: names in SystemPagesGroup should be in request.dicts

        Get a list of all pages, and check that the dicts list all of them.

        Assume that the SystemPagesGroup is in the data or the underlay dir.
        """
        assert Page.Page(self.request, 'SystemPagesGroup').exists(), \
               "SystemPagesGroup is missing, Can't run test"
        systemPages = wikidicts.Group(self.request, 'SystemPagesGroup')
        for member in systemPages.members():
            self.assert_(self.request.dicts.has_member('SystemPagesGroup', member),
                         '%s should be in request.dict' % member)    
