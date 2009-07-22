# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search Tests

    @copyright: 2005 by Nir Soffer <nirs@freeshell.org>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py

from MoinMoin.search import QueryError
from MoinMoin.search.queryparser import QueryParser
from MoinMoin.search import Xapian
from MoinMoin import search
from MoinMoin._tests import nuke_xapian_index

class TestQueryParsing:
    """ search: query parser tests """

    def testQueryParser(self):
        """ search: test the query parser """
        parser = QueryParser()
        for query, wanted in [
            # Even a single term is a and expression (this is needed for xapian because it
            # only has AND_NOT, but not a simple NOT).  This is why we have many many brackets here.
            ("a", '["a"]'),
            ("-a", '[-"a"]'),
            ("a b", '["a" "b"]'),
            ("a -b c", '["a" -"b" "c"]'),
            ("aaa bbb -ccc", '["aaa" "bbb" -"ccc"]'),
            ("title:aaa title:bbb -title:ccc", '[title:"aaa" title:"bbb" -title:"ccc"]'),
            ("title:case:aaa title:re:bbb -title:re:case:ccc", '[title:case:"aaa" title:re:"bbb" -title:re:case:"ccc"]'),
            ("linkto:aaa", '[linkto:"aaa"]'),
            ("category:aaa", '[category:"aaa"]'),
            ("domain:aaa", '[domain:"aaa"]'),
            ("re:case:title:aaa", '[title:re:case:"aaa"]'),
            ("(aaa or bbb) and (ccc or ddd)", '[[[["aaa"] or ["bbb"]]] [[["ccc"] or ["ddd"]]]]'),
            ("(aaa or bbb) (ccc or ddd)", '[[[["aaa"] or ["bbb"]]] [[["ccc"] or ["ddd"]]]]'),
            ("aaa or bbb", '[[["aaa"] or ["bbb"]]]'),
            ("aaa or bbb or ccc", '[[["aaa"] or [[["bbb"] or ["ccc"]]]]]'),
            ("aaa or bbb and ccc", '[[["aaa"] or ["bbb" "ccc"]]]'),
            ("aaa and bbb or ccc", '[[["aaa" "bbb"] or ["ccc"]]]'),
            ("aaa and bbb and ccc", '["aaa" "bbb" "ccc"]'),
            ("aaa or bbb and ccc or ddd", '[[["aaa"] or [[["bbb" "ccc"] or ["ddd"]]]]]'),
            ("aaa or bbb ccc or ddd", '[[["aaa"] or [[["bbb" "ccc"] or ["ddd"]]]]]'),
            ("(HelpOn) (Administration)", '[["HelpOn"] ["Administration"]]'),
            ("(HelpOn) (-Administration)", '[["HelpOn"] [-"Administration"]]'),
            ("(HelpOn) and (-Administration)", '[["HelpOn"] [-"Administration"]]'),
            ("(HelpOn) and (Administration) or (Configuration)", '[[[["HelpOn"] ["Administration"]] or [["Configuration"]]]]'),
            ("(a) and (b) or (c) or -d", '[[[["a"] ["b"]] or [[[["c"]] or [-"d"]]]]]'),
            ("a b c d e or f g h", '[[["a" "b" "c" "d" "e"] or ["f" "g" "h"]]]'),
            ('"no', '[""no"]'),
            ('no"', '["no""]'),
            ("'no", "[\"'no\"]"),
            ("no'", "[\"no'\"]"),
            ('"no\'', '[""no\'"]')
            ]:
            result = parser.parse_query(query)
            assert str(result) == wanted

    def testQueryParserExceptions(self):
        """ search: test the query parser """
        parser = QueryParser()
        def _test(q):
            py.test.raises(QueryError, parser.parse_query, q)
        for query in ['""', '(', ')', '(a or b']:
            yield _test, query

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
        result = search.searchPages(self.request, u"title:HelpOn -title:AccessControlLists")
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


class TestXapianIndex:
    """ search: test Xapian indexing """

    def testIndex(self):
        """ search: kicks off indexing for a single pages in Xapian """
        # This only tests that the call to indexing doesn't raise.
        nuke_xapian_index(self.request)
        idx = Xapian.Index(self.request)
        idx.indexPages(mode='add') # slow: builds an index of all pages

    def testIndexInNewThread(self):
        """ search: kicks off indexing for a page in a new thread in Xapian"""
        # This only tests that the call to indexing doesn't raise.
        nuke_xapian_index(self.request)
        idx = Xapian.Index(self.request)
        idx.indexPagesInNewThread(mode='add') # slow: builds an index of all pages

coverage_modules = ['MoinMoin.search']

