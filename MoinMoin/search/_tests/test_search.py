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
from MoinMoin._tests import nuke_xapian_index, wikiconfig, become_trusted, create_page, nuke_page


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

    pages = {'SearchTestPage': 'this is test page',
             'SearchTestLinks': 'SearchTestPage',
             'SearchTestLinksLowerCase': 'searchtestpage',
             'SearchTestOtherLinks': 'SearchTestLinks'}

    def setup_class(self):
        become_trusted(self.request)

        for page, text in self.pages.iteritems():
            create_page(self.request, page, text)

    def teardown_class(self):
        for page in self.pages:
            nuke_page(self.request, page)

    def search(self, query):
        return search.searchPages(self.request, query)

    def test_title_search_simple(self):
        result = self.search(u'title:SearchTestPage')
        assert len(result.hits) == 1

        result = self.search(u'title:LanguageSetup')
        assert len(result.hits) == 1

        result = self.search(u'title:SearchTestNotExisting')
        assert not result.hits

    def test_title_search_re(self):
        result = self.search(ur'title:re:\bSearchTest')
        assert len(result.hits) == 4

        result = self.search(ur'title:re:\bSearchTest\b')
        assert not result.hits

    def test_title_search_case(self):
        result = self.search(u'title:case:SearchTestPage')
        assert len(result.hits) == 1

        result = self.search(u'title:case:searchtestpage')
        assert not result.hits

    def test_title_search_case_re(self):
        result = self.search(ur'title:case:re:\bSearchTestPage\b')
        assert len(result.hits) == 1

        result = self.search(ur'title:case:re:\bsearchtestpage\b')
        assert not result.hits

    def test_linkto_search_simple(self):
        result = self.search(u'linkto:SearchTestPage')
        assert len(result.hits) == 1

        result = self.search(u'linkto:SearchTestNotExisting')
        assert not result.hits

    def test_linkto_search_re(self):
        result = self.search(ur'linkto:re:\bSearchTest')
        assert len(result.hits) == 2

        result = self.search(ur'linkto:re:\bSearchTest\b')
        assert not result.hits

    def test_linkto_search_case(self):
        result = self.search(u'linkto:case:SearchTestPage')
        assert len(result.hits) == 1

        result = self.search(u'linkto:case:searchtestpage')
        assert not result.hits

    def test_linkto_search_case_re(self):
        result = self.search(ur'linkto:case:re:\bSearchTestPage\b')
        assert len(result.hits) == 1

        result = self.search(ur'linkto:case:re:\bsearchtestpage\b')
        assert not result.hits

    def test_category_search_simple(self):
        result = self.search(u'category:CategoryHomepage')
        assert result.hits

        result = self.search(u'category:CategorySearchTestNotExisting')
        assert not result.hits

    def test_category_search_re(self):
        result = self.search(ur'category:re:\bCategoryHomepage\b')
        assert result.hits

        result = self.search(ur'category:re:\bCategoryHomepa\b')
        assert not result.hits

    def test_category_search_case(self):
        result = self.search(u'category:case:CategoryHomepage')
        assert result.hits

        result = self.search(u'category:case:categoryhomepage')
        assert not result.hits

    def test_category_search_case_re(self):
        result = self.search(ur'category:case:re:\bCategoryHomepage\b')
        assert result.hits

        result = self.search(ur'category:case:re:\bcategoryhomepage\b')
        assert not result.hits

    def test_mimetype_search_simple(self):
        result = self.search(u'mimetype:text/text')
        assert result.hits

    def test_mimetype_search_re(self):
        result = self.search(ur'mimetype:re:\btext/text\b')
        assert result.hits

        result = self.search(ur'category:re:\bCategoryHomepa\b')
        assert not result.hits

    def test_language_search_simple(self):
        result = self.search(u'language:en')
        assert result.hits

    def test_domain_search_simple(self):
        result = self.search(u'domain:system')
        assert result.hits

    def testTitleSearchAND(self):
        """ search: title search with AND expression """
        result = search.searchPages(self.request, u"title:Help title:Index")
        assert len(result.hits) == 1

        result = search.searchPages(self.request, u"title:Help title:%s" % self.doesnotexist)
        assert not result.hits

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

    def setup_method(self, method):

        py.test.importorskip('MoinMoin.support.xappy')
        from MoinMoin.search.Xapian import Index, MoinIndexerConnection

        nuke_xapian_index(self.request)

        index = Index(self.request)
        assert index.lock.acquire(1.0)
        try:
            connection = MoinIndexerConnection(index.dir)
            index._unsign()
            for page in self.pages:
                index._index_page(self.request, connection, page, mode='add')
            index._sign()
        finally:
            index.lock.release()
            connection.close()

    def teardown_method(self, method):
        nuke_xapian_index(self.request)


class TestXapianIndexingInNewThread(object):
    """ search: test Xapian indexing """

    def test_index_in_new_thread(self):
        """ search: kicks off indexing for a single pages in Xapian """
        py.test.skip('XXX takes a lot of time')

        py.test.importorskip('MoinMoin.support.xappy')
        from MoinMoin.search import Xapian

        # This only tests that the call to indexing doesn't raise.
        nuke_xapian_index(self.request)
        idx = Xapian.Index(self.request)
        idx.indexPagesInNewThread(mode='add') # slow: builds an index of all pages

        nuke_xapian_index(self.request)


coverage_modules = ['MoinMoin.search']

