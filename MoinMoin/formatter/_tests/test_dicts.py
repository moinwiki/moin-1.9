# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.formatter.dicts Tests

    @copyright: 2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""


from  MoinMoin.formatter.dicts import Formatter
from MoinMoin.Page import Page
from MoinMoin._tests import become_trusted, create_page, nuke_page


class TestDictFormatter(object):

    def get_dict(self, text):
        request = self.request
        formatter = Formatter(self.request)

        become_trusted(request)
        create_page(request, u'TestPageDict', text)
        page = Page(request, 'TestPageDict', formatter=formatter)
        page.send_page(content_only=True)
        nuke_page(request, u'TestPageDict')

        return formatter.dict

    def test_simple(self):
        text = """
 One:: 1
 Two:: 2
"""
        dict = self.get_dict(text)
        assert len(dict) == 2
        assert dict['One'] == '1'
        assert dict['Two'] == '2'

    def test_complex(self):
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
        dict = self.get_dict(text)
        assert len(dict) == 4
        assert dict['First'] == 'first item'
        assert dict['text with spaces'] == 'second item'
        assert dict['Empty string'] == ''
        assert dict['Last'] == 'last item'


coverage_modules = ['MoinMoin.formtter.dicts']

