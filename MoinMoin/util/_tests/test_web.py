# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.util.web Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.util import web
from MoinMoin.widget import html


class TestMakeQueryString:
    """util.web: making query string"""

    def testMakeQueryStringFromArgument(self):
        """ util.web: make query sting from argument """
        tests = (
            # description,          arg,                expected
            ('string unchanged',    'a=b',              'a=b'),
            ('string value',        {'a': 'b'},         'a=b'),
            ('integer value',       {'a': 1},           'a=1'),
            ('multiply values',     {'a': 1, 'b': 2},   'a=1&b=2'),
            )

        for description, arg, expected in tests:
            assert wikiutil.makeQueryString(arg) == expected

    def testMakeQueryStringFromKeywords(self):
        """ util.web: make query sting from keywords """
        assert wikiutil.makeQueryString(a=1, b='string') == 'a=1&b=string'

    def testMakeQueryStringFromArgumentAndKeywords(self):
        """ util.web: make query sting from argument and keywords """

        tests = (
            # description,      arg,                    expected
            ('kw ignored',      'a=1',                  'a=1'),
            ('kw added to arg', {'a': 1},               'a=1&b=kw'),
            ('kw override arg', {'a': 1, 'b': 'arg'},   'a=1&b=kw'),
            )

        for description, arg, expected in tests:
            # Call makeQueryString with both arg and keyword
            assert wikiutil.makeQueryString(arg, b='kw') == expected


class TestMakeSelection:
    """util.web: creating html select"""

    values = ('one', 'two', 'simple', ('complex', 'A tuple & <escaped text>'))

    html._SORT_ATTRS = 1
    expected = (
        u'<select name="test" size="1">'
        u'<option value="one">one</option>'
        u'<option value="two">two</option>'
        u'<option value="simple">simple</option>'
        u'<option value="complex">A tuple &amp; &lt;escaped text&gt;</option>'
        u'</select>'
    )

    def testMakeSelectNoSelection(self):
        """util.web: creating html select with no selection"""
        expected = self.expected
        result = unicode(web.makeSelection('test', self.values, size=1))
        assert result == expected

    def testMakeSelectNoSelection2(self):
        """util.web: creating html select with non existing selection"""
        expected = self.expected
        result = unicode(web.makeSelection('test', self.values, 'three', size=1))
        assert result == expected

    def testMakeSelectWithSelectedItem(self):
        """util.web: creating html select with selected item"""
        expected = self.expected.replace('value="two"', 'selected value="two"')
        result = unicode(web.makeSelection('test', self.values, 'two', size=1))
        assert result == expected


coverage_modules = ['MoinMoin.util.web']

