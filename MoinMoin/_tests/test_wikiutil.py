# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikiutil Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin import wikiutil


class TestQueryStringSupport:
    tests = [
        ('', {}, {}),
        ('key1=value1', {'key1': 'value1'}, {'key1': u'value1'}),
        ('key1=value1&key2=value2', {'key1': 'value1', 'key2': 'value2'}, {'key1': u'value1', 'key2': u'value2'}),
        ('rc_de=Aktuelle%C3%84nderungen', {'rc_de': 'Aktuelle\xc3\x84nderungen'}, {'rc_de': u'Aktuelle\xc4nderungen'}),
    ]
    def testParseQueryString(self):
        for qstr, expected_str, expected_unicode in self.tests:
            assert wikiutil.parseQueryString(qstr, want_unicode=False) == expected_str
            assert wikiutil.parseQueryString(qstr, want_unicode=True) == expected_unicode
            assert wikiutil.parseQueryString(unicode(qstr), want_unicode=False) == expected_str
            assert wikiutil.parseQueryString(unicode(qstr), want_unicode=True) == expected_unicode

    def testMakeQueryString(self):
        for qstr, in_str, in_unicode in self.tests:
            assert wikiutil.parseQueryString(wikiutil.makeQueryString(in_unicode, want_unicode=False), want_unicode=False) == in_str
            assert wikiutil.parseQueryString(wikiutil.makeQueryString(in_str, want_unicode=False), want_unicode=False) == in_str
            assert wikiutil.parseQueryString(wikiutil.makeQueryString(in_unicode, want_unicode=True), want_unicode=True) == in_unicode
            assert wikiutil.parseQueryString(wikiutil.makeQueryString(in_str, want_unicode=True), want_unicode=True) == in_unicode


class TestTickets:
    def testTickets(self):
        from MoinMoin.Page import Page
        # page name with double quotes
        self.request.page = Page(self.request, u'bla"bla')
        ticket1 = wikiutil.createTicket(self.request)
        assert wikiutil.checkTicket(self.request, ticket1)
        # page name with non-ASCII chars
        self.request.page = Page(self.request, u'\xc4rger')
        ticket2 = wikiutil.createTicket(self.request)
        assert wikiutil.checkTicket(self.request, ticket2)
        # same page with another action
        self.request.page = Page(self.request, u'\xc4rger')
        self.request.action = 'another'
        ticket3 = wikiutil.createTicket(self.request)
        assert wikiutil.checkTicket(self.request, ticket3)

        assert ticket1 != ticket2
        assert ticket2 != ticket3


class TestCleanInput:
    def testCleanInput(self):
        tests = [(u"", u""), # empty
                 (u"aaa\r\n\tbbb", u"aaa   bbb"), # ws chars -> blanks
                 (u"aaa\x00\x01bbb", u"aaabbb"), # strip weird chars
                 (u"a"*500, u""), # too long
                ]
        for instr, outstr in tests:
            assert wikiutil.clean_input(instr) == outstr


class TestNameQuoting:
    tests = [(u"", u'""'), # empty
             (u"test", u'"test"'), # nothing special
             (u"Sarah O'Connor", u"\"Sarah O'Connor\""),
             (u'Just "something" quoted', u'"Just ""something"" quoted"'),
            ]
    def testQuoteName(self):
        for name, qname in self.tests:
            assert wikiutil.quoteName(name) == qname

    def testUnquoteName(self):
        for name, qname in self.tests:
            assert wikiutil.unquoteName(qname) == name


class TestInterWiki:
    def testSplitWiki(self):
        tests = [('SomePage', ('Self', 'SomePage', '')),
                 ('OtherWiki:OtherPage', ('OtherWiki', 'OtherPage', '')),
                 ('MoinMoin:"Page with blanks" link title', ("MoinMoin", "Page with blanks", "link title")),
                 ('MoinMoin:"Page with blanks"link title', ("MoinMoin", "Page with blanks", "link title")),
                 ('MoinMoin:"Page with blanks"', ("MoinMoin", "Page with blanks", "")),
                 ('MoinMoin:"Page with ""quote""" link title', ("MoinMoin", 'Page with "quote"', "link title")),
                 ('MoinMoin:"Page with """"double-quote"""link title', ("MoinMoin", 'Page with ""double-quote"', "link title")),
                 ('MoinMoin:"""starts with quote"link title', ("MoinMoin", '"starts with quote', "link title")),
                 ('MoinMoin:"ends with quote"""link title', ("MoinMoin", 'ends with quote"', "link title")),
                 ('MoinMoin:"""page with quotes around"""link title', ("MoinMoin", '"page with quotes around"', "link title")),
                 ('attachment:"filename with blanks.txt" other title', ("attachment", "filename with blanks.txt", "other title")),
                ]
        for markup, (wikiname, pagename, linktext) in tests:
            assert wikiutil.split_wiki(markup) == (wikiname, pagename, linktext)

    def testJoinWiki(self):
        tests = [(('http://example.org/', u'SomePage'), 'http://example.org/SomePage'),
                 (('http://example.org/?page=$PAGE&action=show', u'SomePage'), 'http://example.org/?page=SomePage&action=show'),
                 (('http://example.org/', u'Aktuelle\xc4nderungen'), 'http://example.org/Aktuelle%C3%84nderungen'),
                 (('http://example.org/$PAGE/show', u'Aktuelle\xc4nderungen'), 'http://example.org/Aktuelle%C3%84nderungen/show'),
                ]
        for (baseurl, pagename), url in tests:
            assert wikiutil.join_wiki(baseurl, pagename) == url


class TestSystemPagesGroup:
    def testSystemPagesGroupNotEmpty(self):
        assert self.request.dicts.members('SystemPagesGroup')

class TestSystemPage:
    systemPages = (
        # First level, on SystemPagesGroup
        'SystemPagesInEnglishGroup',
        # Second level, on one of the pages above
        'RecentChanges',
        'TitleIndex',
        )
    notSystemPages = (
        'NoSuchPageYetAndWillNeverBe',
        )

    def testSystemPage(self):
        """wikiutil: good system page names accepted, bad rejected"""
        for name in self.systemPages:
            assert wikiutil.isSystemPage(self.request, name)
        for name in self.notSystemPages:
            assert not  wikiutil.isSystemPage(self.request, name)


class TestTemplatePage:
    good = (
        'aTemplate',
        'MyTemplate',
    )
    bad = (
        'Template',
        'ATemplate',
        'TemplateInFront',
        'xTemplateInFront',
        'XTemplateInFront',
    )

    def testTemplatePage(self):
        """wikiutil: good template names accepted, bad rejected"""
        for name in self.good:
            assert  wikiutil.isTemplatePage(self.request, name)
        for name in self.bad:
            assert not wikiutil.isTemplatePage(self.request, name)


class TestParmeterParser:

    def testParameterParser(self):
        tests = [
            # trivial
            ('', '', 0, {}),

            # fixed
            ('%s%i%f%b', '"test",42,23.0,True', 4, {0: 'test', 1: 42, 2: 23.0, 3: True}),

            # fixed and named
            ('%s%(x)i%(y)i', '"test"', 1, {0: 'test', 'x': None, 'y': None}),
            ('%s%(x)i%(y)i', '"test",1', 1, {0: 'test', 'x': 1, 'y': None}),
            ('%s%(x)i%(y)i', '"test",1,2', 1, {0: 'test', 'x': 1, 'y': 2}),
            ('%s%(x)i%(y)i', '"test",x=1', 1, {0: 'test', 'x': 1, 'y': None}),
            ('%s%(x)i%(y)i', '"test",x=1,y=2', 1, {0: 'test', 'x': 1, 'y': 2}),
            ('%s%(x)i%(y)i', '"test",y=2', 1, {0: 'test', 'x': None, 'y': 2}),

            # test mixed acceptance
            ("%ifs", '100', 1, {0: 100}),
            ("%ifs", '100.0', 1, {0: 100.0}),
            ("%ifs", '"100"', 1, {0: "100"}),

            # boolean
            ("%(t)b%(f)b", '', 0, {'t': None, 'f': None}),
            ("%(t)b%(f)b", 't=1', 0, {'t': True, 'f': None}),
            ("%(t)b%(f)b", 'f=False', 0, {'t': None, 'f': False}),
            ("%(t)b%(f)b", 't=True, f=0', 0, {'t': True, 'f': False}),

            # integer
            ("%(width)i%(height)i", '', 0, {'width': None, 'height': None}),
            ("%(width)i%(height)i", 'width=100', 0, {'width': 100, 'height': None}),
            ("%(width)i%(height)i", 'height=200', 0, {'width': None, 'height': 200}),
            ("%(width)i%(height)i", 'width=100, height=200', 0, {'width': 100, 'height': 200}),

            # float
            ("%(width)f%(height)f", '', 0, {'width': None, 'height': None}),
            ("%(width)f%(height)f", 'width=100.0', 0, {'width': 100.0, 'height': None}),
            ("%(width)f%(height)f", 'height=2.0E2', 0, {'width': None, 'height': 200.0}),
            ("%(width)f%(height)f", 'width=1000.0E-1, height=200.0', 0, {'width': 100.0, 'height': 200.0}),

            # string
            ("%(width)s%(height)s", '', 0, {'width': None, 'height': None}),
            ("%(width)s%(height)s", 'width="really wide"', 0, {'width': 'really wide', 'height': None}),
            ("%(width)s%(height)s", 'height="not too high"', 0, {'width': None, 'height': 'not too high'}),
            ("%(width)s%(height)s", 'width="really wide", height="not too high"', 0, {'width': 'really wide', 'height': 'not too high'}),
            # conversion from given type to expected type
            ("%(width)s%(height)s", 'width=100', 0, {'width': '100', 'height': None}),
            ("%(width)s%(height)s", 'width=100, height=200', 0, {'width': '100', 'height': '200'}),

            # complex test
            ("%i%sf%s%ifs%(a)s|%(b)s", ' 4,"DI\'NG", b=retry, a="DING"', 2, {0: 4, 1: "DI'NG", 'a': 'DING', 'b': 'retry'}),

            ]
        for format, args, expected_fixed_count, expected_dict in tests:
            argParser = wikiutil.ParameterParser(format)
            fixed_count, arg_dict = argParser.parse_parameters(args)
            assert (fixed_count, arg_dict) == (expected_fixed_count, expected_dict)

    def testTooMuchWantedArguments(self):
        args = 'width=100, height=200, alt=Example'
        argParser = wikiutil.ParameterParser("%(width)s%(height)s")
        py.test.raises(ValueError, argParser.parse_parameters, args)

    def testMalformedArguments(self):
        args = '='
        argParser = wikiutil.ParameterParser("%(width)s%(height)s")
        py.test.raises(ValueError, argParser.parse_parameters, args)

    def testWrongTypeFixedPosArgument(self):
        args = '0.0'
        argParser = wikiutil.ParameterParser("%b")
        py.test.raises(ValueError, argParser.parse_parameters, args)

    def testWrongTypeNamedArgument(self):
        args = 'flag=0.0'
        argParser = wikiutil.ParameterParser("%(flag)b")
        py.test.raises(ValueError, argParser.parse_parameters, args)


class TestParamParsing:
    def testMacroArgs(self):
        abcd = [u'a', u'b', u'c', u'd']
        abcd_dict = {u'a': u'1', u'b': u'2', u'c': u'3', u'd': u'4'}
        tests = [
                  # regular and quoting tests
                  (u'd = 4,c=3,b=2,a= 1 ',    ([], abcd_dict, [])),
                  (u'a,b,c,d',                (abcd, {}, [])),
                  (u' a , b , c , d ',        (abcd, {}, [])),
                  (u'   a   ',                ([u'a'], {}, [])),
                  (u'"  a  "',                ([u'  a  '], {}, [])),
                  (u'a,b,c,d, "a,b,c,d"',     (abcd+[u'a,b,c,d'], {}, [])),
                  (u'quote " :), b',          ([u'quote " :)', u'b'], {}, [])),
                  (u'"quote "" :)", b',       ([u'quote " :)', u'b'], {}, [])),
                  (u'=7',                     ([], {u'': u'7'}, [])),
                  (u',,',                     ([None, None, None], {}, [])),
                  (u',"",',                   ([None, u'', None], {}, [])),
                  (u',"", ""',                ([None, u'', u''], {}, [])),
                  (u'  ""  ,"", ""',          ([u'', u'', u''], {}, [])),
                  # some name=value test
                  (u'd = 4,c=3,b=2,a= 1 ',    ([], abcd_dict, [])),
                  (u'd=d,e="a,b,c,d"',        ([], {u'd': u'd',
                                                    u'e': u'a,b,c,d'}, [])),
                  (u'd = d,e = "a,b,c,d"',    ([], {u'd': u'd',
                                                    u'e': u'a,b,c,d'}, [])),
                  (u'd = d, e = "a,b,c,d"',   ([], {u'd': u'd',
                                                    u'e': u'a,b,c,d'}, [])),
                  (u'd = , e = "a,b,c,d"',    ([], {u'd': None,
                                                    u'e': u'a,b,c,d'}, [])),
                  (u'd = "", e = "a,b,c,d"',  ([], {u'd': u'',
                                                    u'e': u'a,b,c,d'}, [])),
                  (u'd = "", e = ',           ([], {u'd': u'', u'e': None},
                                               [])),
                  (u'd=""',                   ([], {u'd': u''}, [])),
                  (u'd = "", e = ""',         ([], {u'd': u'', u'e': u''},
                                               [])),
                  # no, None as key isn't accepted
                  (u' = "",  e = ""',         ([], {u'': u'', u'e': u''},
                                               [])),
                  # can quote both name and value:
                  (u'd = d," e "= "a,b,c,d"', ([], {u'd': u'd',
                                                    u' e ': u'a,b,c,d'}, [])),
                  # trailing args
                  (u'1,2,a=b,3,4',            ([u'1', u'2'], {u'a': u'b'},
                                               [u'3', u'4'])),
                  # can quote quotes:
                  (u'd = """d"',              ([], {u'd': u'"d'}, [])),
                  (u'd = """d"""',            ([], {u'd': u'"d"'}, [])),
                  (u'd = "d"" ", e=7',        ([], {u'd': u'd" ', u'e': u'7'},
                                               [])),
                  (u'd = "d""", e=8',         ([], {u'd': u'd"', u'e': u'8'},
                                               [])),
                ]
        for args, expected in tests:
            result = wikiutil.parse_quoted_separated(args)
            assert expected == result
            for val in result[0]:
                assert val is None or isinstance(val, unicode)
            for val in result[1].keys():
                assert val is None or isinstance(val, unicode)
            for val in result[1].values():
                assert val is None or isinstance(val, unicode)
            for val in result[2]:
                assert val is None or isinstance(val, unicode)

    def testLimited(self):
        tests = [
                  # regular and quoting tests
                  (u'd = 4,c=3,b=2,a= 1 ',    ([], {u'd': u'4',
                                                    u'c': u'3,b=2,a= 1'}, [])),
                  (u'a,b,c,d',                ([u'a', u'b,c,d'], {}, [])),
                  (u'a=b,b,c,d',              ([], {u'a': u'b'}, [u'b,c,d'])),
                ]
        for args, expected in tests:
            result = wikiutil.parse_quoted_separated(args, seplimit=1)
            assert expected == result
            for val in result[0]:
                assert val is None or isinstance(val, unicode)
            for val in result[1].keys():
                assert val is None or isinstance(val, unicode)
            for val in result[1].values():
                assert val is None or isinstance(val, unicode)
            for val in result[2]:
                assert val is None or isinstance(val, unicode)

    def testNoNameValue(self):
        abcd = [u'a', u'b', u'c', u'd']
        tests = [
                  # regular and quoting tests
                  (u'd = 4,c=3,b=2,a= 1 ',    [u'd = 4', u'c=3',
                                               u'b=2', u'a= 1']),
                  (u'a,b,c,d',                abcd),
                  (u' a , b , c , d ',        abcd),
                  (u'   a   ',                [u'a']),
                  (u'"  a  "',                [u'  a  ']),
                  (u'a,b,c,d, "a,b,c,d"',     abcd + [u'a,b,c,d']),
                  (u'quote " :), b',          [u'quote " :)', u'b']),
                  (u'"quote "" :)", b',       [u'quote " :)', u'b']),
                  (u'd=d,e="a,b,c,d"',        [u'd=d', u'e="a', u'b',
                                               u'c', u'd"']),
                ]
        for args, expected in tests:
            result = wikiutil.parse_quoted_separated(args, name_value=False)
            assert expected == result
            for val in result:
                assert val is None or isinstance(val, unicode)


class TestArgGetters:
    def testGetBoolean(self):
        tests = [
            # default testing for None value
            (None, None, None, None),
            (None, None, False, False),
            (None, None, True, True),

            # some real values
            (u'0', None, None, False),
            (u'1', None, None, True),
            (u'false', None, None, False),
            (u'true', None, None, True),
            (u'FALSE', None, None, False),
            (u'TRUE', None, None, True),
            (u'no', None, None, False),
            (u'yes', None, None, True),
            (u'NO', None, None, False),
            (u'YES', None, None, True),
        ]
        for arg, name, default, expected in tests:
            assert wikiutil.get_bool(self.request, arg, name, default) == expected

    def testGetBooleanRaising(self):
        # wrong default type
        py.test.raises(AssertionError, wikiutil.get_bool, self.request, None, None, 42)

        # anything except None or unicode raises TypeError
        py.test.raises(TypeError, wikiutil.get_bool, self.request, True)
        py.test.raises(TypeError, wikiutil.get_bool, self.request, 42)
        py.test.raises(TypeError, wikiutil.get_bool, self.request, 42.0)
        py.test.raises(TypeError, wikiutil.get_bool, self.request, '')
        py.test.raises(TypeError, wikiutil.get_bool, self.request, tuple())
        py.test.raises(TypeError, wikiutil.get_bool, self.request, [])
        py.test.raises(TypeError, wikiutil.get_bool, self.request, {})

        # any value not convertable to boolean raises ValueError
        py.test.raises(ValueError, wikiutil.get_bool, self.request, u'')
        py.test.raises(ValueError, wikiutil.get_bool, self.request, u'42')
        py.test.raises(ValueError, wikiutil.get_bool, self.request, u'wrong')
        py.test.raises(ValueError, wikiutil.get_bool, self.request, u'"True"') # must not be quoted!

    def testGetInt(self):
        tests = [
            # default testing for None value
            (None, None, None, None),
            (None, None, -23, -23),
            (None, None, 42, 42),

            # some real values
            (u'0', None, None, 0),
            (u'42', None, None, 42),
            (u'-23', None, None, -23),
        ]
        for arg, name, default, expected in tests:
            assert wikiutil.get_int(self.request, arg, name, default) == expected

    def testGetIntRaising(self):
        # wrong default type
        py.test.raises(AssertionError, wikiutil.get_int, self.request, None, None, 42.23)

        # anything except None or unicode raises TypeError
        py.test.raises(TypeError, wikiutil.get_int, self.request, True)
        py.test.raises(TypeError, wikiutil.get_int, self.request, 42)
        py.test.raises(TypeError, wikiutil.get_int, self.request, 42.0)
        py.test.raises(TypeError, wikiutil.get_int, self.request, '')
        py.test.raises(TypeError, wikiutil.get_int, self.request, tuple())
        py.test.raises(TypeError, wikiutil.get_int, self.request, [])
        py.test.raises(TypeError, wikiutil.get_int, self.request, {})

        # any value not convertable to int raises ValueError
        py.test.raises(ValueError, wikiutil.get_int, self.request, u'')
        py.test.raises(ValueError, wikiutil.get_int, self.request, u'23.42')
        py.test.raises(ValueError, wikiutil.get_int, self.request, u'wrong')
        py.test.raises(ValueError, wikiutil.get_int, self.request, u'"4711"') # must not be quoted!

    def testGetFloat(self):
        tests = [
            # default testing for None value
            (None, None, None, None),
            (None, None, -23.42, -23.42),
            (None, None, 42.23, 42.23),

            # some real values
            (u'0', None, None, 0),
            (u'42.23', None, None, 42.23),
            (u'-23.42', None, None, -23.42),
            (u'-23.42E3', None, None, -23.42E3),
            (u'23.42E-3', None, None, 23.42E-3),
        ]
        for arg, name, default, expected in tests:
            assert wikiutil.get_float(self.request, arg, name, default) == expected

    def testGetFloatRaising(self):
        # wrong default type
        py.test.raises(AssertionError, wikiutil.get_float, self.request, None, None, u'42')

        # anything except None or unicode raises TypeError
        py.test.raises(TypeError, wikiutil.get_float, self.request, True)
        py.test.raises(TypeError, wikiutil.get_float, self.request, 42)
        py.test.raises(TypeError, wikiutil.get_float, self.request, 42.0)
        py.test.raises(TypeError, wikiutil.get_float, self.request, '')
        py.test.raises(TypeError, wikiutil.get_float, self.request, tuple())
        py.test.raises(TypeError, wikiutil.get_float, self.request, [])
        py.test.raises(TypeError, wikiutil.get_float, self.request, {})

        # any value not convertable to int raises ValueError
        py.test.raises(ValueError, wikiutil.get_float, self.request, u'')
        py.test.raises(ValueError, wikiutil.get_float, self.request, u'wrong')
        py.test.raises(ValueError, wikiutil.get_float, self.request, u'"47.11"') # must not be quoted!

    def testGetUnicode(self):
        tests = [
            # default testing for None value
            (None, None, None, None),
            (None, None, u'', u''),
            (None, None, u'abc', u'abc'),

            # some real values
            (u'', None, None, u''),
            (u'abc', None, None, u'abc'),
            (u'"abc"', None, None, u'"abc"'),
        ]
        for arg, name, default, expected in tests:
            assert wikiutil.get_unicode(self.request, arg, name, default) == expected

    def testGetUnicodeRaising(self):
        # wrong default type
        py.test.raises(AssertionError, wikiutil.get_unicode, self.request, None, None, 42)

        # anything except None or unicode raises TypeError
        py.test.raises(TypeError, wikiutil.get_unicode, self.request, True)
        py.test.raises(TypeError, wikiutil.get_unicode, self.request, 42)
        py.test.raises(TypeError, wikiutil.get_unicode, self.request, 42.0)
        py.test.raises(TypeError, wikiutil.get_unicode, self.request, '')
        py.test.raises(TypeError, wikiutil.get_unicode, self.request, tuple())
        py.test.raises(TypeError, wikiutil.get_unicode, self.request, [])
        py.test.raises(TypeError, wikiutil.get_unicode, self.request, {})


def _test_invoke_int(i=int):
    assert i == 1


def _test_invoke_int_fixed(a, b, i=int):
    assert a == 7
    assert b == 8
    assert i == 1 or i is None


class TestExtensionInvoking:
    def _test_invoke_bool(self, b=bool):
        assert b == False

    def _test_invoke_bool_def(self, v=bool, b=False):
        assert b == v
        assert isinstance(b, bool)
        assert isinstance(v, bool)

    def _test_invoke_int_None(self, i=int):
        assert i == 1 or i is None

    def _test_invoke_float_None(self, i=float):
        assert i == 1.4 or i is None

    def _test_invoke_choice(self, a, choice=[u'a', u'b', u'c']):
        assert a == 7
        assert choice == u'a'

    def _test_invoke_choicet(self, a, choice=(u'a', u'b', u'c')):
        assert a == 7
        assert choice == u'a'

    def _test_trailing(self, a, _trailing_args=[]):
        assert _trailing_args == [u'a']

    def _test_arbitrary_kw(self, expect, _non_ascii_kwargs={}, **kw):
        assert _non_ascii_kwargs == expect
        assert kw == {'test': u'x'}

    def testInvoke(self):
        ief = wikiutil.invoke_extension_function
        ief(self.request, self._test_invoke_bool, u'False')
        ief(self.request, self._test_invoke_bool, u'b=False')
        ief(self.request, _test_invoke_int, u'1')
        ief(self.request, _test_invoke_int, u'i=1')
        ief(self.request, self._test_invoke_bool_def, u'False, False')
        ief(self.request, self._test_invoke_bool_def, u'b=False, v=False')
        ief(self.request, self._test_invoke_bool_def, u'False')
        ief(self.request, self._test_invoke_int_None, u'i=1')
        ief(self.request, self._test_invoke_int_None, u'i=')
        ief(self.request, self._test_invoke_int_None, u'')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_int_None, u'x')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_int_None, u'""')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_int_None, u'i=""')
        py.test.raises(TypeError, ief, self.request,
                       _test_invoke_int_fixed, u'a=7', [7, 8])
        ief(self.request, _test_invoke_int_fixed, u'i=1', [7, 8])
        py.test.raises(ValueError, ief, self.request,
                       _test_invoke_int_fixed, u'i=""', [7, 8])
        ief(self.request, _test_invoke_int_fixed, u'i=', [7, 8])

        for choicefn in (self._test_invoke_choice, self._test_invoke_choicet):
            ief(self.request, choicefn, u'', [7])
            ief(self.request, choicefn, u'choice=a', [7])
            ief(self.request, choicefn, u'choice=', [7])
            ief(self.request, choicefn, u'choice="a"', [7])
            py.test.raises(ValueError, ief, self.request,
                           choicefn, u'x', [7])
            py.test.raises(ValueError, ief, self.request,
                           choicefn, u'choice=x', [7])

        ief(self.request, self._test_invoke_float_None, u'i=1.4')
        ief(self.request, self._test_invoke_float_None, u'i=')
        ief(self.request, self._test_invoke_float_None, u'')
        ief(self.request, self._test_invoke_float_None, u'1.4')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_float_None, u'x')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_float_None, u'""')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_float_None, u'i=""')
        ief(self.request, self._test_trailing, u'a=7, a')
        ief(self.request, self._test_arbitrary_kw, u'test=x, \xc3=test',
            [{u'\xc3': 'test'}])
        ief(self.request, self._test_arbitrary_kw, u'test=x, "\xc3"=test',
            [{u'\xc3': 'test'}])
        ief(self.request, self._test_arbitrary_kw, u'test=x, "7 \xc3"=test',
            [{u'7 \xc3': 'test'}])
        ief(self.request, self._test_arbitrary_kw, u'test=x, 7 \xc3=test',
            [{u'7 \xc3': 'test'}])
        ief(self.request, self._test_arbitrary_kw, u'7 \xc3=test, test= x ',
            [{u'7 \xc3': 'test'}])

coverage_modules = ['MoinMoin.wikiutil']
