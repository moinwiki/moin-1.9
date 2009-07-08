# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.datasttructs.backends._formatters Tests

    @copyright: 2009 by MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.datastruct.backends._formatters import GroupFormatter
from MoinMoin.Page import Page
from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestDatastruct(object):

    def test_CamelCase(self):
        text = """
 * CamelCase
"""
        assert u'CamelCase' in self.get_group(text)

    def test_extended_name(self):
        text = """
 * extended name
"""
        assert u'extended name' in self.get_group(text)

    def test_extended_link(self):
        text = """
 * [[extended link]]
"""
        assert u'extended link' in self.get_group(text)

    def test_extended_link_with_label(self):
        text = """
 * [[extended link| label]]
"""
        assert u'extended link' in self.get_group(text)

    def test_extended_link_and_text(self):
        text = """
 * [[extended link]] other text
 * other text [[extended link]]
 * other text [[extended link]] other text

"""
        assert len(self.get_group(text)) == 0

    def test_ignore_second_level_list(self):
        text = """
  * second level
   * third level
    * forth level
     * and then some...
"""
        assert len([x for x in self.get_group(text)]) == 0

    def test_ignore_other(self):
        text = """
= ignore this =
 * take this

Ignore previous line and this text.
"""
        assert u'take this' in self.get_group(text)

    def test_strip_whitespace(self):
        text = """
 *   take this
"""
        assert u'take this' in self.get_group(text)

    def get_group(self, text):
        request = self.request
        formatter = GroupFormatter(self.request)

        become_trusted(request)
        create_page(request, u'TestPageGroup', text)
        page = Page(request, 'TestPageGroup', formatter=formatter)
        page.send_page(content_only=True)
        nuke_page(request, u'TestPageGroup')

        return formatter.members

