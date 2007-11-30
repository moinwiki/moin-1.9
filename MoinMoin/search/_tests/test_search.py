# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search Tests

    @copyright: 2005 by Nir Soffer <nirs@freeshell.org>
    @license: GNU GPL, see COPYING for details.
"""

import pprint

from MoinMoin import search


class TestQuotingBug:
    """search: quoting bug tests

    http://moinmoin.wikiwikiweb.de/MoinMoinBugs/SearchOneCharString
    """

    def testIsQuoted(self):
        """ search: quoting bug - quoted terms """
        parser = search.QueryParser()
        for case in ('"yes"', "'yes'"):
            assert parser.isQuoted(case)

    def testIsNotQuoted(self):
        """ search: quoting bug - unquoted terms """
        tests = ('', "'", '"', '""', "''", "'\"", '"no', 'no"', "'no", "no'", '"no\'')
        parser = search.QueryParser()
        for case in tests:
            assert not parser.isQuoted(case)


class TestQueryParsing:
    """ search: query parser tests """

    def testQueryParser(self):
        """ search: ... """
        parser = search.QueryParser()
        for query, wanted in [
            ("a", '"a"'),
            ("a b", '["a" "b"]'),
            ("a -b c", '["a" -"b" "c"]'),
            ("aaa bbb -ccc", '["aaa" "bbb" -"ccc"]'),
            ("aaa OR bbb", '["aaa" "OR" "bbb"]'),
            ]:
            result = parser.parse_query(query)
            assert str(result) == wanted


coverage_modules = ['MoinMoin.search']

