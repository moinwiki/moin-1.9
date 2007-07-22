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
                ]
        for args, expected in tests:
            result = wikiutil.parse_quoted_separated(args)
            assert expected == result

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


coverage_modules = ['MoinMoin.wikiutil']
