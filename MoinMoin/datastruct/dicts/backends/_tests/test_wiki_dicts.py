# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.datastruct.dicts.backends.wiki_dicts tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.datastruct.dicts.backends import wiki_dicts
from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestDictDict:

    def setup_class(self):
        request = self.request
        become_trusted(request)

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

        create_page(request, u'SomeTestDict', text)

    def teardown_class(self):
        become_trusted(self.request)
        nuke_page(self.request, u'SomeTestDict')

    def test_getitem(self):
        dicts = self.request.dicts

        some_test_dict = dicts['SomeTestDict']
        assert len(some_test_dict) == 4
        assert some_test_dict['First'] == 'first item'
        assert some_test_dict['text with spaces'] == 'second item'
        assert some_test_dict['Empty string'] == '' # XXX fails if trailing blank is missing
        assert some_test_dict['Last'] == 'last item'

    def test_contains(self):
        dicts = self.request.dicts

        assert  u'SomeTestDict' in dicts
        assert u'SomeNotExistingDict' not in dicts


coverage_modules = ['MoinMoin.datastruct.dicts.backends.wiki_dicts']

