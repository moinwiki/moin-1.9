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
from MoinMoin import search
from MoinMoin._tests import nuke_xapian_index, wikiconfig


class TestQueryParsing(object):
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
            ('"no\'', '[""no\'"]')]:
            result = parser.parse_query(query)
            assert str(result) == wanted

    def testQueryParserExceptions(self):
        """ search: test the query parser """
        parser = QueryParser()

        def _test(q):
            py.test.raises(QueryError, parser.parse_query, q)

        for query in ['""', '(', ')', '(a or b']:
            yield _test, query


class TestSearch(object):
    """ search: test search """
    doesnotexist = u'jfhsdaASDLASKDJ'

    def test_prefix_search(self):

        def simple_test(prefix, term):
            result = search.searchPages(self.request, u"%s:%s" % (prefix, term))
            assert result.hits
            result = search.searchPages(self.request, u"%s:%s" % (prefix, self.doesnotexist))
            assert not result.hits

        def re_test(prefix, term):
            result = search.searchPages(self.request, ur"%s:re:\b%s\b" % (prefix, term))
            assert result.hits
            result = search.searchPages(self.request, ur"%s:re:\b%s\b" % (prefix, self.doesnotexist))
            assert not result.hits

        def case_test(prefix, term):
            result = search.searchPages(self.request, u"%s:case:%s" % (prefix, term))
            assert result.hits
            result = search.searchPages(self.request, u"%s:case:%s" % (prefix, term.lower()))
            assert not result.hits

        def case_re_test(prefix, term):
            result = search.searchPages(self.request, ur"%s:case:re:\%s\b" % (prefix, term))
            assert result.hits
            result = search.searchPages(self.request, ur"%s:case:re:\%s\b" % (prefix, term.lower()))
            assert not result.hits

        for prefix, term in [('title', 'FrontPage'), ('linkto', 'FrontPage'), ('category', 'CategoryHomepage')]:
            for test in [simple_test, re_test, case_test, case_re_test]:
                yield '%s %s' % (prefix, test.func_name), test, prefix, term

        for prefix, term in [('mimetype', 'text/text')]:
            for test in [simple_test, re_test]:
                yield '%s %s' % (prefix, test.func_name), test, prefix, term

        for prefix, term in [('language', 'en'), ('domain', 'system')]:
            for test in [simple_test]:
                yield '%s %s' % (prefix, test.func_name), test, prefix, term

    def testTitleSearchAND(self):
        """ search: title search with AND expression """
        result = search.searchPages(self.request, u"title:Help title:Index")
        assert len(result.hits) == 1

        result = search.searchPages(self.request, u"title:Help title:%s" % self.doesnotexist)
        assert len(result.hits) == 0

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

    def test_title_search(self):

        query = QueryParser(titlesearch=True).parse_query('Moin')
        result = search.searchPages(self.request, query, sort='page_name')


class TestXapianSearch(TestSearch):
    """ search: test Xapian indexing """

    class Config(wikiconfig.Config):

        xapian_search = True

    def setup_class(self):
        """ search: kicks off indexing for a single pages in Xapian """

        py.test.importorskip('xappy')


        # This only tests that the call to indexing doesn't raise.
        nuke_xapian_index(self.request)
        idx = Xapian.Index(self.request)
        idx.indexPages(mode='add') # slow: builds an index of all pages

    def teardown_class(self):
        nuke_xapian_index(self.request)


class TestXapianIndexingInNewThread(object):
    """ search: test Xapian indexing """

    def setup_class(self):
        """ search: kicks off indexing for a single pages in Xapian """

        py.test.importorskip('xappy')

        # This only tests that the call to indexing doesn't raise.
        nuke_xapian_index(self.request)
        idx = Xapian.Index(self.request)
        idx.indexPagesInNewThread(mode='add') # slow: builds an index of all pages

    def teardown_class(self):
        nuke_xapian_index(self.request)


coverage_modules = ['MoinMoin.search']

