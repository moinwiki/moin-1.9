# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikixml.marshal Tests

    @copyright: 2002-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import array
from MoinMoin.wikixml import marshal

class TestMarshal(object):
    """Testing Marshal used for ...XXX"""

    class Data:
        cvar = 'Class Variable'
        def __init__(self, value):
            self.ivar = value

    prop = (
        # value, xml representation in a marshal object
        (None, '<data><prop><none/></prop></data>'),
        ("string", '<data><prop>string</prop></data>'),
        ([1, "abc"], '<data><prop><item>1</item><item>abc</item></prop></data>'),
        ((1, "abc"), '<data><prop><item>1</item><item>abc</item></prop></data>'),
        ({"abc": 1}, '<data><prop><abc>1</abc></prop></data>'),
        (1, '<data><prop>1</prop></data>'),
        (Data('value'), '<data><prop><data><ivar>value</ivar></data></prop></data>'),
        (array.array("i", [42]), "<data><prop>array('i', [42])</prop></data>"),
        (buffer("0123456789", 2, 3), "<data><prop>234</prop></data>"),
        )

    def setup_method(self, method):
        self.obj = marshal.Marshal()

    def testCreateMarshal(self):
        """wikixml.marshal: create new marshal"""
        self._checkData(self.obj, '<data></data>')

    def testSetMarshalProperty(self):
        """wikixml.marshal: setting marshal property"""
        for value, xml in self.prop:
            self.obj.prop = value
            self._checkData(self.obj, xml)

    def _canonize(self, xml):
        xml = xml.replace('\n', '')
        return xml

    def _checkData(self, obj, xml):
        objXML = self._canonize(obj.toXML())
        expected = self._canonize(xml)
        assert objXML == expected


coverage_modules = ['MoinMoin.wikixml.marshal']

