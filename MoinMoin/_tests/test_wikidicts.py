# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikidicts tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py
import re
import shutil

from MoinMoin import wikidicts
from MoinMoin import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.user import User
from MoinMoin._tests import append_page, become_trusted, create_page, create_random_string_list, nuke_page, nuke_user


class TestDictPage:

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
 Empty string::\x20
 Last:: last item
'''
        d = wikidicts.Dict(self.request, '')
        d.initFromText(text)
        assert d['First'] == 'first item'
        assert d['text with spaces'] == 'second item'
        assert d['Empty string'] == '' # XXX fails if trailing blank is missing
        assert d['Last'] == 'last item'
        assert len(d) == 4


coverage_modules = ['MoinMoin.wikidicts']

