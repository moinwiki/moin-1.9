# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.widget.html Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest # LEGACY UNITTEST, PLEASE DO NOT IMPORT unittest IN NEW TESTS, PLEASE CONSULT THE py.test DOCS
from MoinMoin.widget import html

class TestHTMLWidgets(unittest.TestCase):
    """widget.html: testing html widgets"""

    def testCreate(self):
        """widget.html: creating html widgets

        TO DO: add tests for all elements by HTML 4 spec.
        """
        tests = (
            # description, call, expected           
            ('Create text', html.Text('<br> &'), '&lt;br&gt; &amp;'),
            ('Create raw html', html.Raw('<br> &amp;'), '<br> &amp;'),
            ('Create br', html.BR(), '<br>'),
            ('Create hr', html.HR(), '<hr>'),
            ('Create p', html.P(), '<p></p>'),
            )

        for description, obj, expected in tests:
            result = unicode(obj)
            self.assertEqual(result, expected,
                             ('%(description)s: expected "%(expected)s" '
                              'but got "%(result)s"') % locals())

    def testInvalidAttributes(self):
        """widegt.html: invalid attributes raises exception

        TO DO: add tests for all elements by HTML 4 spec.
        """
        self.assertRaises(AttributeError, html.BR, name='foo')


    def testCompositeElements(self):
        """widget.html: append to and extend composite element"""
        html._SORT_ATTRS = 1
        element = html.P()

        actions = (
            # action, data, expected
            (element.append,
             html.Text('Text & '),
             '<p>Text &amp; </p>'),
            (element.append,
             html.Text('more text. '),
             '<p>Text &amp; more text. </p>'),
            (element.extend,
             (html.Text('And then '), html.Text('some.')),
             '<p>Text &amp; more text. And then some.</p>'),
            )

        for action, data, expected in actions:
            action(data)
            result = unicode(element)
            self.assertEqual(result, expected,
                             'Expected "%(expected)s" but got "%(result)s"' % locals())

