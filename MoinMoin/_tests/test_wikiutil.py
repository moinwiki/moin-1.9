# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikiutil Tests

    @copyright: 2003-2004 by Juergen Hermann <jh@web.de>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin import config, wikiutil

from werkzeug import MultiDict


class TestQueryStringSupport:
    tests = [
        ('', {}, {}),
        ('key1=value1', {'key1': 'value1'}, {'key1': u'value1'}),
        ('key1=value1&key2=value2', {'key1': 'value1', 'key2': 'value2'}, {'key1': u'value1', 'key2': u'value2'}),
        ('rc_de=Aktuelle%C3%84nderungen', {'rc_de': 'Aktuelle\xc3\x84nderungen'}, {'rc_de': u'Aktuelle\xc4nderungen'}),
    ]
    def testParseQueryString(self):
        for qstr, expected_str, expected_unicode in self.tests:
            assert wikiutil.parseQueryString(qstr) == MultiDict(expected_unicode)
            assert wikiutil.parseQueryString(unicode(qstr)) == MultiDict(expected_unicode)

    def testMakeQueryString(self):
        for qstr, in_str, in_unicode in self.tests:
            assert wikiutil.parseQueryString(wikiutil.makeQueryString(in_unicode)) == MultiDict(in_unicode)
            assert wikiutil.parseQueryString(wikiutil.makeQueryString(in_str)) == MultiDict(in_unicode)


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


class TestInterWiki:
    def testSplitWiki(self):
        tests = [('SomePage', ('Self', 'SomePage')),
                 ('OtherWiki:OtherPage', ('OtherWiki', 'OtherPage')),
                 (':OtherPage', ('', 'OtherPage')),
                 # broken ('/OtherPage', ('Self', '/OtherPage')),
                 # wrong interpretation ('MainPage/OtherPage', ('Self', 'MainPage/OtherPage')),
                ]
        for markup, (wikiname, pagename) in tests:
            assert wikiutil.split_wiki(markup) == (wikiname, pagename)

    def testJoinWiki(self):
        tests = [(('http://example.org/', u'SomePage'), 'http://example.org/SomePage'),
                 (('http://example.org/?page=$PAGE&action=show', u'SomePage'), 'http://example.org/?page=SomePage&action=show'),
                 (('http://example.org/', u'Aktuelle\xc4nderungen'), 'http://example.org/Aktuelle%C3%84nderungen'),
                 (('http://example.org/$PAGE/show', u'Aktuelle\xc4nderungen'), 'http://example.org/Aktuelle%C3%84nderungen/show'),
                ]
        for (baseurl, pagename), url in tests:
            assert wikiutil.join_wiki(baseurl, pagename) == url


class TestSystemPage:
    systemPages = (
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
        'I want a Template',
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

    def testDoubleNameValueSeparator(self):
        tests = [
                  # regular and quoting tests
                  (u'd==4,=3 ',    ([], {u'd': u'=4', u'': u'3'}, [])),
                  (u'===a,b,c,d',  ([], {u'': u'==a'}, [u'b', u'c', u'd'])),
                  (u'a,b,===,c,d', ([u'a', u'b'], {u'': u'=='}, [u'c', u'd'])),
                ]

        def _check(a, e):
            r = wikiutil.parse_quoted_separated(a)
            assert r == e

        for args, expected in tests:
            yield _check, args, expected

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
                  (u'"unended quote',         [u'"unended quote']),
                  (u'"',                      [u'"']),
                  (u'd=d,e="a,b,c,d"',        [u'd=d', u'e="a', u'b',
                                               u'c', u'd"']),
                ]
        for args, expected in tests:
            result = wikiutil.parse_quoted_separated(args, name_value=False)
            assert expected == result
            for val in result:
                assert val is None or isinstance(val, unicode)

    def testUnitArgument(self):
        result = wikiutil.UnitArgument('7mm', float, ['%', 'mm'])
        assert result.get_default() ==  (7.0, 'mm')
        assert result.parse_argument('8%') == (8.0, '%')
        py.test.raises(ValueError, result.parse_argument,  u'7m')
        py.test.raises(ValueError, result.parse_argument,  u'7')
        py.test.raises(ValueError, result.parse_argument,  u'mm')

    def testExtendedParser(self):
        tests = [
            (u'"a", "b", "c"', u',', None, [u'a', u'b', u'c']),
            (u'a:b, b:c, c:d', u',', u':', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'a:b, b:c, c:d', u',', None, [u'a:b', u'b:c', u'c:d']),
            (u'a=b, b=c, c=d', u',', None, [u'a=b', u'b=c', u'c=d']),
            (u'a=b, b=c, c=d', u',', u'=', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'"a"; "b"; "c"', u';', None, [u'a', u'b', u'c']),
            (u'a:b; b:c; c:d', u';', u':', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'a:b; b:c; c:d', u';', None, [u'a:b', u'b:c', u'c:d']),
            (u'a=b; b=c; c=d', u';', None, [u'a=b', u'b=c', u'c=d']),
            (u'a=b; b=c; c=d', u';', u'=', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'"a" "b" "c"', None, None, [u'a', u'b', u'c']),
            (u'" a " "b" "c"', None, None, [u' a ', u'b', u'c']),
            (u'"a  " "b" "c"', None, None, [u'a  ', u'b', u'c']),
            (u'"  a" "b" "c"', None, None, [u'  a', u'b', u'c']),
            (u'"  a" "b" "c"', None, u':', [u'  a', u'b', u'c']),
            (u'"a:a" "b:b" "c:b"', None, u':', [u'a:a', u'b:b', u'c:b']),
            (u'   a:a  ', None, u':', [None, None, None, (u'a', u'a'), None, None]),
            (u'a a: a', None, u':', [u'a', (u'a', None), u'a']),
            (u'a a:"b c d" a', None, u':', [u'a', (u'a', u'b c d'), u'a']),
            (u'a a:"b "" d" a', None, u':', [u'a', (u'a', u'b " d'), u'a']),
            (u'title:Help* dog cat', None, u':', [(u'title', u'Help*'), u'dog', u'cat']),
            (u'title:Help* "dog cat"', None, u':', [(u'title', u'Help*'), u'dog cat']),
            (u'a:b:c d:e:f', None, u':', [(u'a', u'b:c'), (u'd', 'e:f')]),
            (u'a:b:c:d', None, u':', [(u'a', u'b:c:d')]),
        ]

        def _check(args, sep, kwsep, expected):
            res = wikiutil.parse_quoted_separated_ext(args, sep, kwsep)
            assert res == expected

        for test in tests:
            yield [_check] + list(test)

    def testExtendedParserBracketing(self):
        tests = [
            (u'"a", "b", "c"', u',', None, [u'a', u'b', u'c']),
            (u'("a", "b", "c")', u',', None, [[u'(', u'a', u'b', u'c']]),
            (u'("a"("b", "c"))', u',', None, [[u'(', u'a', [u'(', u'b', u'c']]]),
            (u'("a"("b)))", "c"))', u',', None, [[u'(', u'a', [u'(', u'b)))', u'c']]]),
            (u'("a"("b>>> ( ab )>", "c"))', u',', None, [[u'(', u'a', [u'(', u'b>>> ( ab )>', u'c']]]),
            (u'("a" ("b" "c"))', None, None, [[u'(', u'a', [u'(', u'b', u'c']]]),
            (u'("a"("b", "c") ) ', u',', None, [[u'(', u'a', [u'(', u'b', u'c']]]),
            (u'("a", <"b", ("c")>)', u',', None, [[u'(', u'a', [u'<', u'b', [u'(', u'c']]]]),
            (u',,,(a, b, c)', u',', None, [None, None, None, [u'(', u'a', u'b', u'c']]),
        ]

        def _check(args, sep, kwsep, expected):
            res = wikiutil.parse_quoted_separated_ext(args, sep, kwsep, brackets=(u'<>', u'()'))
            assert res == expected

        for test in tests:
            yield [_check] + list(test)

    def testExtendedParserQuoting(self):
        tests = [
            (u'"a b" -a b-', u'"', [u'a b', u'-a', u'b-']),
            (u'"a b" -a b-', u"-", [u'"a', u'b"', u'a b']),
            (u'"a b" -a b-', u'"-', [u'a b', u'a b']),
            (u'"a- b" -a b-', u'"-', [u'a- b', u'a b']),
            (u'"a- b" -a" b-', u'"-', [u'a- b', u'a" b']),
        ]

        def _check(args, quotes, expected):
            res = wikiutil.parse_quoted_separated_ext(args, quotes=quotes)
            assert res == expected

        for test in tests:
            yield [_check] + list(test)

    def testExtendedParserMultikey(self):
        tests = [
            (u'"a", "b", "c"', u',', None, [u'a', u'b', u'c']),
            (u'a:b, b:c, c:d', u',', u':', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'a:b, b:c, c:d', u',', None, [u'a:b', u'b:c', u'c:d']),
            (u'a=b, b=c, c=d', u',', None, [u'a=b', u'b=c', u'c=d']),
            (u'a=b, b=c, c=d', u',', u'=', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'"a"; "b"; "c"', u';', None, [u'a', u'b', u'c']),
            (u'a:b; b:c; c:d', u';', u':', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'a:b; b:c; c:d', u';', None, [u'a:b', u'b:c', u'c:d']),
            (u'a=b; b=c; c=d', u';', None, [u'a=b', u'b=c', u'c=d']),
            (u'a=b; b=c; c=d', u';', u'=', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'"a" "b" "c"', None, None, [u'a', u'b', u'c']),
            (u'" a " "b" "c"', None, None, [u' a ', u'b', u'c']),
            (u'"a  " "b" "c"', None, None, [u'a  ', u'b', u'c']),
            (u'"  a" "b" "c"', None, None, [u'  a', u'b', u'c']),
            (u'"  a" "b" "c"', None, u':', [u'  a', u'b', u'c']),
            (u'"a:a" "b:b" "c:b"', None, u':', [u'a:a', u'b:b', u'c:b']),
            (u'   a:a  ', None, u':', [None, None, None, (u'a', u'a'), None, None]),
            (u'a a: a', None, u':', [u'a', (u'a', None), u'a']),
            (u'a a:"b c d" a', None, u':', [u'a', (u'a', u'b c d'), u'a']),
            (u'a a:"b "" d" a', None, u':', [u'a', (u'a', u'b " d'), u'a']),
            (u'title:Help* dog cat', None, u':', [(u'title', u'Help*'), u'dog', u'cat']),
            (u'title:Help* "dog cat"', None, u':', [(u'title', u'Help*'), u'dog cat']),
            (u'a:b:c d:e:f', None, u':', [(u'a', u'b', u'c'), (u'd', 'e', u'f')]),
            (u'a:b:c:d', None, u':', [(u'a', u'b', u'c', u'd')]),
            (u'a:"b:c":d', None, u':', [(u'a', u'b:c', u'd')]),
        ]

        def _check(args, sep, kwsep, expected):
            res = wikiutil.parse_quoted_separated_ext(args, sep, kwsep, multikey=True)
            assert res == expected

        for test in tests:
            yield [_check] + list(test)

    def testExtendedParserPrefix(self):
        P = wikiutil.ParserPrefix('+')
        M = wikiutil.ParserPrefix('-')
        tests = [
            (u'"a", "b", "c"', u',', None, [u'a', u'b', u'c']),
            (u'a:b, b:c, c:d', u',', u':', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'a:b, b:c, c:d', u',', None, [u'a:b', u'b:c', u'c:d']),
            (u'a=b, b=c, c=d', u',', None, [u'a=b', u'b=c', u'c=d']),
            (u'a=b, b=c, c=d', u',', u'=', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'"a"; "b"; "c"', u';', None, [u'a', u'b', u'c']),
            (u'a:b; b:c; c:d', u';', u':', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'a:b; b:c; c:d', u';', None, [u'a:b', u'b:c', u'c:d']),
            (u'a=b; b=c; c=d', u';', None, [u'a=b', u'b=c', u'c=d']),
            (u'a=b; b=c; c=d', u';', u'=', [(u'a', u'b'), (u'b', u'c'), (u'c', u'd')]),
            (u'"a" "b" "c"', None, None, [u'a', u'b', u'c']),
            (u'" a " "b" "c"', None, None, [u' a ', u'b', u'c']),
            (u'"a  " "b" "c"', None, None, [u'a  ', u'b', u'c']),
            (u'"  a" "b" "c"', None, None, [u'  a', u'b', u'c']),
            (u'"  a" "b" "c"', None, u':', [u'  a', u'b', u'c']),
            (u'"a:a" "b:b" "c:b"', None, u':', [u'a:a', u'b:b', u'c:b']),
            (u'   a:a  ', None, u':', [None, None, None, (u'a', u'a'), None, None]),
            (u'a a: a', None, u':', [u'a', (u'a', None), u'a']),
            (u'a a:"b c d" a', None, u':', [u'a', (u'a', u'b c d'), u'a']),
            (u'a a:"b "" d" a', None, u':', [u'a', (u'a', u'b " d'), u'a']),
            (u'title:Help* dog cat', None, u':', [(u'title', u'Help*'), u'dog', u'cat']),
            (u'title:Help* "dog cat"', None, u':', [(u'title', u'Help*'), u'dog cat']),
            (u'a:b:c d:e:f', None, u':', [(u'a', u'b', u'c'), (u'd', 'e', u'f')]),
            (u'a:b:c:d', None, u':', [(u'a', u'b', u'c', u'd')]),
            (u'a:"b:c":d', None, u':', [(u'a', u'b:c', u'd')]),

            (u'-a:b:d', None, u':', [(M, u'a', u'b', u'd')]),
            (u'"-a:b:d"', None, u':', [(u'-a:b:d')]),
            (u'-"a:b:d"', None, u':', [(M, u'a:b:d')]),
            (u'-a:"b:c":"d e f g"', None, u':', [(M, u'a', u'b:c', u'd e f g')]),
            (u'+-a:b:d', None, u':', [(P, u'-a', u'b', u'd')]),
            (u'-"+a:b:d"', None, u':', [(M, u'+a:b:d')]),
            # bit of a weird case...
            (u'-+"a:b:d"', None, u':', [(M, u'+"a', u'b', u'd"')]),
            (u'-a:"b:c" a +b', None, u':', [(M, u'a', u'b:c'), u'a', (P, u'b')]),
        ]

        def _check(args, sep, kwsep, expected):
            res = wikiutil.parse_quoted_separated_ext(args, sep, kwsep, multikey=True, prefixes='-+')
            assert res == expected

        for test in tests:
            yield [_check] + list(test)

    def testExtendedParserBracketingErrors(self):
        UCE = wikiutil.BracketUnexpectedCloseError
        MCE = wikiutil.BracketMissingCloseError
        tests = [
            (u'("a", "b", "c"', u',', None, MCE),
            (u'("a"("b", "c")', u',', None, MCE),
            (u'("a"<"b", "c")>', u',', None, UCE),
            (u')("a" ("b" "c"))', None, None, UCE),
            (u'("a", ("b", "c">))', u',', None, UCE),
            (u'("a", ("b", <"c">>))', u',', None, UCE),
            (u'(<(<)>)>', u',', None, UCE),
        ]

        def _check(args, sep, kwsep, err):
            py.test.raises(err,
                           wikiutil.parse_quoted_separated_ext,
                           args, sep, kwsep,
                           brackets=(u'<>', u'()'))

        for test in tests:
            yield [_check] + list(test)

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

    def testGetComplex(self):
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
            (u'23.42E-3+3.04j', None, None, 23.42E-3+3.04j),
            (u'3.04j', None, None, 3.04j),
            (u'-3.04j', None, None, -3.04j),
            (u'23.42E-3+3.04i', None, None, 23.42E-3+3.04j),
            (u'3.04i', None, None, 3.04j),
            (u'-3.04i', None, None, -3.04j),
            (u'-3', None, None, -3L),
            (u'-300000000000000000000', None, None, -300000000000000000000L),
        ]
        for arg, name, default, expected in tests:
            assert wikiutil.get_complex(self.request, arg, name, default) == expected

    def testGetComplexRaising(self):
        # wrong default type
        py.test.raises(AssertionError, wikiutil.get_complex, self.request, None, None, u'42')

        # anything except None or unicode raises TypeError
        py.test.raises(TypeError, wikiutil.get_complex, self.request, True)
        py.test.raises(TypeError, wikiutil.get_complex, self.request, 42)
        py.test.raises(TypeError, wikiutil.get_complex, self.request, 42.0)
        py.test.raises(TypeError, wikiutil.get_complex, self.request, 3j)
        py.test.raises(TypeError, wikiutil.get_complex, self.request, '')
        py.test.raises(TypeError, wikiutil.get_complex, self.request, tuple())
        py.test.raises(TypeError, wikiutil.get_complex, self.request, [])
        py.test.raises(TypeError, wikiutil.get_complex, self.request, {})

        # any value not convertable to int raises ValueError
        py.test.raises(ValueError, wikiutil.get_complex, self.request, u'')
        py.test.raises(ValueError, wikiutil.get_complex, self.request, u'3jj')
        py.test.raises(ValueError, wikiutil.get_complex, self.request, u'3Ij')
        py.test.raises(ValueError, wikiutil.get_complex, self.request, u'3i-3i')
        py.test.raises(ValueError, wikiutil.get_complex, self.request, u'wrong')
        py.test.raises(ValueError, wikiutil.get_complex, self.request, u'"47.11"') # must not be quoted!

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


class TestExtensionInvoking:
    def _test_invoke_bool(self, b=bool):
        assert b is False

    def _test_invoke_bool_def(self, v=bool, b=False):
        assert b == v
        assert isinstance(b, bool)
        assert isinstance(v, bool)

    def _test_invoke_int_None(self, i=int):
        assert i == 1 or i is None

    def _test_invoke_float_None(self, i=float):
        assert i == 1.4 or i is None

    def _test_invoke_float_required(self, i=wikiutil.required_arg(float)):
        assert i == 1.4

    def _test_invoke_choice(self, a, choice=[u'a', u'b', u'c']):
        assert a == 7
        assert choice == u'a'

    def _test_invoke_choicet(self, a, choice=(u'a', u'b', u'c')):
        assert a == 7
        assert choice == u'a'

    def _test_invoke_choice_required(self, i=wikiutil.required_arg((u'b', u'a'))):
        assert i == u'a'

    def _test_trailing(self, a, _trailing_args=[]):
        assert _trailing_args == [u'a']

    def _test_arbitrary_kw(self, expect, _kwargs={}):
        assert _kwargs == expect

    def testInvoke(self):
        def _test_invoke_int(i=int):
            assert i == 1

        def _test_invoke_int_fixed(a, b, i=int):
            assert a == 7
            assert b == 8
            assert i == 1 or i is None

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
        py.test.raises(ValueError, ief, self.request,
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
        ief(self.request, self._test_trailing, u'7, a')
        ief(self.request, self._test_arbitrary_kw, u'test=x, \xc3=test',
            [{u'\xc3': 'test', 'test': u'x'}])
        ief(self.request, self._test_arbitrary_kw, u'test=x, "\xc3"=test',
            [{u'\xc3': 'test', 'test': u'x'}])
        ief(self.request, self._test_arbitrary_kw, u'test=x, "7 \xc3"=test',
            [{u'7 \xc3': 'test', 'test': u'x'}])
        ief(self.request, self._test_arbitrary_kw, u'test=x, 7 \xc3=test',
            [{u'7 \xc3': 'test', 'test': u'x'}])
        ief(self.request, self._test_arbitrary_kw, u'7 \xc3=test, test= x ',
            [{u'7 \xc3': 'test', 'test': u'x'}])
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_float_required, u'')
        ief(self.request, self._test_invoke_float_required, u'1.4')
        ief(self.request, self._test_invoke_float_required, u'i=1.4')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_choice_required, u'')
        ief(self.request, self._test_invoke_choice_required, u'a')
        ief(self.request, self._test_invoke_choice_required, u'i=a')
        py.test.raises(ValueError, ief, self.request,
                       self._test_invoke_float_required, u',')

    def testConstructors(self):
        ief = wikiutil.invoke_extension_function

        # new style class
        class TEST1(object):
            def __init__(self, a=int):
                self.constructed = True
                assert a == 7

        class TEST2(TEST1):
            pass

        obj = ief(self.request, TEST1, u'a=7')
        assert isinstance(obj, TEST1)
        assert obj.constructed
        py.test.raises(ValueError, ief, self.request, TEST1, u'b')

        obj = ief(self.request, TEST2, u'a=7')
        assert isinstance(obj, TEST1)
        assert isinstance(obj, TEST2)
        assert obj.constructed
        py.test.raises(ValueError, ief, self.request, TEST2, u'b')

        # old style class
        class TEST3:
            def __init__(self, a=int):
                self.constructed = True
                assert a == 7

        class TEST4(TEST3):
            pass

        obj = ief(self.request, TEST3, u'a=7')
        assert isinstance(obj, TEST3)
        assert obj.constructed
        py.test.raises(ValueError, ief, self.request, TEST3, u'b')

        obj = ief(self.request, TEST4, u'a=7')
        assert isinstance(obj, TEST3)
        assert isinstance(obj, TEST4)
        assert obj.constructed
        py.test.raises(ValueError, ief, self.request, TEST4, u'b')

    def testFailing(self):
        ief = wikiutil.invoke_extension_function

        py.test.raises(TypeError, ief, self.request, hex, u'15')
        py.test.raises(TypeError, ief, self.request, cmp, u'15')
        py.test.raises(AttributeError, ief, self.request, unicode, u'15')

    def testAllDefault(self):
        ief = wikiutil.invoke_extension_function

        def has_many_defaults(a=1, b=2, c=3, d=4):
            assert a == 1
            assert b == 2
            assert c == 3
            assert d == 4
            return True

        assert ief(self.request, has_many_defaults, u'1, 2, 3, 4')
        assert ief(self.request, has_many_defaults, u'2, 3, 4', [1])
        assert ief(self.request, has_many_defaults, u'3, 4', [1, 2])
        assert ief(self.request, has_many_defaults, u'4', [1, 2, 3])
        assert ief(self.request, has_many_defaults, u'', [1, 2, 3, 4])
        assert ief(self.request, has_many_defaults, u'd=4,c=3,b=2,a=1')
        assert ief(self.request, has_many_defaults, u'd=4,c=3,b=2', [1])
        assert ief(self.request, has_many_defaults, u'd=4,c=3', [1, 2])
        assert ief(self.request, has_many_defaults, u'd=4', [1, 2, 3])

    def testInvokeComplex(self):
        ief = wikiutil.invoke_extension_function

        def has_complex(a=complex, b=complex):
            assert a == b
            return True

        assert ief(self.request, has_complex, u'3-3i, 3-3j')
        assert ief(self.request, has_complex, u'2i, 2j')
        assert ief(self.request, has_complex, u'b=2i, a=2j')
        assert ief(self.request, has_complex, u'2.007, 2.007')
        assert ief(self.request, has_complex, u'2.007', [2.007])
        assert ief(self.request, has_complex, u'b=2.007', [2.007])


class TestAnchorNames:
    def test_anchor_name_encoding(self):
        tests = [
            # text                    expected output
            (u'\xf6\xf6ll\xdf\xdf',   'A.2BAPYA9g-ll.2BAN8A3w-'),
            (u'level 2',              'level_2'),
            (u'level_2',              'level_2'),
            (u'',                     'A'),
            (u'123',                  'A123'),
            # make sure that a valid anchor is not modified:
            (u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:_.-',
             u'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:_.-')
        ]
        for text, expected in tests:
            yield self._check, text, expected

    def _check(self, text, expected):
        encoded = wikiutil.anchor_name_from_text(text)
        assert expected == encoded

class TestPageLinkMarkup:
    def test_pagelinkmarkup(self):
        tests = [
            # pagename (no link text), expected markup
            (('SomePage', ), 'SomePage'),
            (('Somepage', ), '[[Somepage]]'),
            (('somepage', ), '[[somepage]]'),
            (('Some Page', ), '[[Some Page]]'),
            # with link text
            (('SomePage', 'SomePage'), 'SomePage'),
            (('SomePage', 'some page'), '[[SomePage|some page]]'),
            (('Some Page', 'Some Page'), '[[Some Page]]'),
            (('Some Page', 'some Page'), '[[Some Page|some Page]]'),
        ]
        for params, expected in tests:
            yield self._check, params, expected

    def _check(self, params, expected):
        assert expected == wikiutil.pagelinkmarkup(*params)

class TestRelativeTools:
    tests = [
        # test                      expected output
        # CHILD_PREFIX
        (('MainPage', '/SubPage1'), 'MainPage/SubPage1'),
        (('MainPage', '/SubPage1/SubPage2'), 'MainPage/SubPage1/SubPage2'),
        (('MainPage/SubPage1', '/SubPage2/SubPage3'), 'MainPage/SubPage1/SubPage2/SubPage3'),
        (('', '/OtherMainPage'), 'OtherMainPage'), # strange
        # PARENT_PREFIX
        (('MainPage/SubPage', '../SisterPage'), 'MainPage/SisterPage'),
        (('MainPage/SubPage1/SubPage2', '../SisterPage'), 'MainPage/SubPage1/SisterPage'),
        (('MainPage/SubPage1/SubPage2', '../../SisterPage'), 'MainPage/SisterPage'),
        (('MainPage', '../SisterPage'), 'SisterPage'), # strange
    ]
    def test_abs_pagename(self):
        for (current_page, relative_page), absolute_page in self.tests:
            yield self._check_abs_pagename, current_page, relative_page, absolute_page

    def _check_abs_pagename(self, current_page, relative_page, absolute_page):
        assert absolute_page == wikiutil.AbsPageName(current_page, relative_page)

    def test_rel_pagename(self):
        for (current_page, relative_page), absolute_page in self.tests:
            yield self._check_rel_pagename, current_page, absolute_page, relative_page

    def _check_rel_pagename(self, current_page, absolute_page, relative_page):
        assert relative_page == wikiutil.RelPageName(current_page, absolute_page)


class TestNormalizePagename(object):

    def testPageInvalidChars(self):
        """ request: normalize pagename: remove invalid unicode chars

        Assume the default setting
        """
        test = u'\u0000\u202a\u202b\u202c\u202d\u202e'
        expected = u''
        result = wikiutil.normalize_pagename(test, self.request.cfg)
        assert result == expected

    def testNormalizeSlashes(self):
        """ request: normalize pagename: normalize slashes """
        cases = (
            (u'/////', u''),
            (u'/a', u'a'),
            (u'a/', u'a'),
            (u'a/////b/////c', u'a/b/c'),
            (u'a b/////c d/////e f', u'a b/c d/e f'),
            )
        for test, expected in cases:
            result = wikiutil.normalize_pagename(test, self.request.cfg)
            assert result == expected

    def testNormalizeWhitespace(self):
        """ request: normalize pagename: normalize whitespace """
        cases = (
            (u'         ', u''),
            (u'    a', u'a'),
            (u'a    ', u'a'),
            (u'a     b     c', u'a b c'),
            (u'a   b  /  c    d  /  e   f', u'a b/c d/e f'),
            # All 30 unicode spaces
            (config.chars_spaces, u''),
            )
        for test, expected in cases:
            result = wikiutil.normalize_pagename(test, self.request.cfg)
            assert result == expected

    def testUnderscoreTestCase(self):
        """ request: normalize pagename: underscore convert to spaces and normalized

        Underscores should convert to spaces, then spaces should be
        normalized, order is important!
        """
        cases = (
            (u'         ', u''),
            (u'  a', u'a'),
            (u'a  ', u'a'),
            (u'a  b  c', u'a b c'),
            (u'a  b  /  c  d  /  e  f', u'a b/c d/e f'),
            )
        for test, expected in cases:
            result = wikiutil.normalize_pagename(test, self.request.cfg)
            assert result == expected

class TestGroupPages(object):

    def testNormalizeGroupName(self):
        """ request: normalize pagename: restrict groups to alpha numeric Unicode

        Spaces should normalize after invalid chars removed!
        """
        cases = (
            # current acl chars
            (u'Name,:Group', u'NameGroup'),
            # remove than normalize spaces
            (u'Name ! @ # $ % ^ & * ( ) + Group', u'Name Group'),
            )
        for test, expected in cases:
            # validate we are testing valid group names
            if wikiutil.isGroupPage(test, self.request.cfg):
                result = wikiutil.normalize_pagename(test, self.request.cfg)
                assert result == expected

class TestVersion(object):
    def test_Version(self):
        Version = wikiutil.Version
        # test properties
        assert Version(1, 2, 3).major == 1
        assert Version(1, 2, 3).minor == 2
        assert Version(1, 2, 3).release == 3
        assert Version(1, 2, 3, '4.5alpha6').additional == '4.5alpha6'
        # test Version init and Version to str conversion
        assert str(Version(1)) == "1.0.0"
        assert str(Version(1, 2)) == "1.2.0"
        assert str(Version(1, 2, 3)) == "1.2.3"
        assert str(Version(1, 2, 3, '4.5alpha6')) == "1.2.3-4.5alpha6"
        assert str(Version(version='1.2.3')) == "1.2.3"
        assert str(Version(version='1.2.3-4.5alpha6')) == "1.2.3-4.5alpha6"
        # test Version comparison, trivial cases
        assert Version() == Version()
        assert Version(1) == Version(1)
        assert Version(1, 2) == Version(1, 2)
        assert Version(1, 2, 3) == Version(1, 2, 3)
        assert Version(1, 2, 3, 'foo') == Version(1, 2, 3, 'foo')
        assert Version(1) != Version(2)
        assert Version(1, 2) != Version(1, 3)
        assert Version(1, 2, 3) != Version(1, 2, 4)
        assert Version(1, 2, 3, 'foo') != Version(1, 2, 3, 'bar')
        assert Version(1) < Version(2)
        assert Version(1, 2) < Version(1, 3)
        assert Version(1, 2, 3) < Version(1, 2, 4)
        assert Version(1, 2, 3, 'bar') < Version(1, 2, 3, 'foo')
        assert Version(2) > Version(1)
        assert Version(1, 3) > Version(1, 2)
        assert Version(1, 2, 4) > Version(1, 2, 3)
        assert Version(1, 2, 3, 'foo') > Version(1, 2, 3, 'bar')
        # test Version comparison, more delicate cases
        assert Version(1, 12) > Version(1, 9)
        assert Version(1, 12) > Version(1, 1, 2)
        assert Version(1, 0, 0, '0.0a2') > Version(1, 0, 0, '0.0a1')
        assert Version(1, 0, 0, '0.0b1') > Version(1, 0, 0, '0.0a9')
        assert Version(1, 0, 0, '0.0b2') > Version(1, 0, 0, '0.0b1')
        assert Version(1, 0, 0, '0.0c1') > Version(1, 0, 0, '0.0b9')
        assert Version(1, 0, 0, '1') > Version(1, 0, 0, '0.0c9')
        # test Version playing nice with tuples
        assert Version(1, 2, 3) == (1, 2, 3, '')
        assert Version(1, 2, 4) > (1, 2, 3)


coverage_modules = ['MoinMoin.wikiutil']

