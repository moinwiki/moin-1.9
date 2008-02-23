# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search Tests

    @copyright: 2005 by Nir Soffer <nirs@freeshell.org>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

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
        """ search: test the query parser """
        parser = search.QueryParser()
        for query, wanted in [
            ("a", '"a"'),
            ("a b", '["a" "b"]'),
            ("a -b c", '["a" -"b" "c"]'),
            ("aaa bbb -ccc", '["aaa" "bbb" -"ccc"]'),
            ("title:aaa title:bbb -title:ccc", '[!"aaa" !"bbb" -!"ccc"]'),
            ("aaa or bbb", '["aaa" or "bbb"]'),
            ("(HelpOn) (Administration)", '["HelpOn" "Administration"]'),
            ("(HelpOn) (-Administration)", '["HelpOn" -"Administration"]'),
            ]:
            result = parser.parse_query(query)
            assert str(result) == wanted


class TestSearch:
    """ search: test search """
    doesnotexist = u'jfhsdaASDLASKDJ'

    def testTitleSearchFrontPage(self):
        """ search: title search for FrontPage """
        result = search.searchPages(self.request, u"title:FrontPage")
        assert len(result.hits) == 1

    def testTitleSearchAND(self):
        """ search: title search with AND expression """
        result = search.searchPages(self.request, u"title:Help title:Index")
        assert len(result.hits) == 1

    def testTitleSearchOR(self):
        """ search: title search with OR expression """
        result = search.searchPages(self.request, u"title:FrontPage or title:RecentChanges")
        assert len(result.hits) == 2

    def testTitleSearchNegatedFindAll(self):
        """ search: negated title search for some pagename that does not exist results in all pagenames """
        result = search.searchPages(self.request, u"-title:%s" % self.doesnotexist)
        assert len(result.hits) > 100 # XXX should be "all"

    def testTitleSearchNegativeTerm(self):
        """ search: title search for a AND expression with a negative term """
        helpon_count = len(search.searchPages(self.request, u"title:HelpOn").hits)
        result = search.searchPages(self.request, u"title:HelpOn -title:Acl")
        assert len(result.hits) == helpon_count - 1 # finds all HelpOn* except one

    def testFullSearchNegatedFindAll(self):
        """ search: negated full search for some string that does not exist results in all pages """
        result = search.searchPages(self.request, u"-%s" % self.doesnotexist)
        assert len(result.hits) > 100 # XXX should be "all"

    def testFullSearchNegativeTerm(self):
        """ search: full search for a AND expression with a negative term """
        helpon_count = len(search.searchPages(self.request, u"HelpOn").hits)
        result = search.searchPages(self.request, u"HelpOn -ACL")
        assert 0 < len(result.hits) < helpon_count


coverage_modules = ['MoinMoin.search']

