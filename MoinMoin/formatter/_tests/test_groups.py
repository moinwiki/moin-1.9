# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.formatter.groups Tests

    @copyright: 2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""

from  MoinMoin.formatter.groups import Formatter
from MoinMoin.Page import Page
from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestGroupFormatter(object):

    def test_CamelCase(self):
        text = """
 * CamelCase
"""
        groups = list(self.get_group(text))
        assert len(groups) == 1
        assert u'CamelCase' in groups

    def test_extended_name(self):
        text = """
 * extended name
"""
        groups = list(self.get_group(text))
        assert len(groups) == 1
        assert u'extended name' in groups

    def test_extended_link(self):
        text = """
 * [[extended link]]
"""
        groups = list(self.get_group(text))
        assert len(groups) == 1
        assert u'extended link' in groups

    def test_extended_link_with_label(self):
        text = """
 * [[extended link| label]]
"""
        groups = list(self.get_group(text))
        assert len(groups) == 1
        assert u'label' in groups

    def test_extended_link_and_text(self):
        text = """
 * [[extended link]] other text
 * other text [[extended link]]
 * other text [[extended link]] other text

"""
        groups = list(self.get_group(text))
        assert len(groups) == 3
        assert u'extended link other text' in groups
        assert u'other text extended link' in groups
        assert u'other text extended link other text' in groups

    def test_ignore_not_first_level_list(self):
        text = """
 * first level
  * second level
   * [[SomeLink]]
    * forth level
     * and then some...
 * again first level
"""
        groups = list(self.get_group(text))
        assert len(groups) == 2
        assert 'first level' in groups
        assert 'again first level' in groups

    def test_intended_list(self):
        text = """
    * first level
     * second level
      * [[SomeLink]]
       * forth level
        * and then some...
    * again first level
"""
        groups = list(self.get_group(text))
        assert len(groups) == 2
        assert 'first level' in groups
        assert 'again first level' in groups

    def test_ignore_other(self):
        text = """
= ignore this =
 * take this

Ignore previous line and this text.
"""
        groups = list(self.get_group(text))
        assert len(groups) == 1
        assert u'take this' in groups

    def test_strip_whitespace(self):
        text = """
 *   take this
"""
        groups = list(self.get_group(text))
        assert len(groups) == 1
        assert u'take this' in groups

    def get_group(self, text):
        request = self.request
        formatter = Formatter(self.request)

        become_trusted(request)
        create_page(request, u'TestPageGroup', text)
        page = Page(request, 'TestPageGroup', formatter=formatter)
        page.send_page(content_only=True)
        nuke_page(request, u'TestPageGroup')

        return formatter.members

coverage_modules = ['MoinMoin.formtter.groups']

