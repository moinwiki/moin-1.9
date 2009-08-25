# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.datastruct.backends.wiki_dicts tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
                2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""


from MoinMoin.datastruct.backends._tests import DictsBackendTest
from MoinMoin.datastruct.backends import wiki_dicts
from MoinMoin._tests import become_trusted, create_page, nuke_page


class TestWikiDictsBackend(DictsBackendTest):

    # Suppose that default configuration for the dicts is used which
    # is WikiDicts backend.

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

        text = """
 One:: 1
 Two:: 2
"""
        create_page(request, u'SomeOtherTestDict', text)

    def teardown_class(self):
        become_trusted(self.request)
        nuke_page(self.request, u'SomeTestDict')
        nuke_page(self.request, u'SomeOtherTestDict')


coverage_modules = ['MoinMoin.datastruct.backends.wiki_dicts']

