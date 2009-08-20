# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search Tests

    @copyright: 2005 by Nir Soffer <nirs@freeshell.org>,
                2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""


import py, os, time

from MoinMoin.search import QueryError
from MoinMoin.search.queryparser import QueryParser
from MoinMoin.search.builtin import MoinSearch, XapianSearch
from MoinMoin._tests import nuke_xapian_index, wikiconfig, become_trusted, create_page, nuke_page

if py.version != '1.0.0':
    # There are some generative tests, which won't run on older versions!
    # XXX These tests should be refactored to be able to be run with older versions of py.
    py.test.skip('Currently py version 1.0.0 is needed')


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


class BaseSearchTest(object):
    """ search: test search """
    doesnotexist = u'jfhsdaASDLASKDJ'

    pages = {u'SearchTestPage': u'this is a test page',
             u'SearchTestLinks': u'SearchTestPage',
             u'SearchTestLinksLowerCase': u'searchtestpage',
             u'SearchTestOtherLinks': u'SearchTestLinks',
             u'LanguageSetup': None,
             u'CategoryHomepage': None,
             u'HomePageWiki': None,
             u'FrontPage': None,
             u'RecentChanges': None,
             u'HelpOnCreoleSyntax': None,
             u'HelpIndex': None}

    def setup_class(self):
        become_trusted(self.request)

        for page, text in self.pages.iteritems():
            if text:
                create_page(self.request, page, text)

    def teardown_class(self):
        for page, text in self.pages.iteritems():
            if text:
                nuke_page(self.request, page)

    def get_searcher(self, query):
        raise NotImplementedError

    def search(self, query):
        if isinstance(query, str) or isinstance(query, unicode):
            query = QueryParser().parse_query(query)

        return self.get_searcher(query).run()

    def test_title_search_simple(self):
        searches = {u'title:SearchTestPage': 1,
                    u'title:LanguageSetup': 1,
                    u'title:HelpIndex': 1,
                    u'title:Help': 2,
                    u'title:SearchTestNotExisting': 0}

        def test(query, res_count):
            result = self.search(query)
            assert len(result.hits) == res_count

        for query, res_count in searches.iteritems():
            yield query, test, query, res_count

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
        assert len(result.hits) == 1

        result = self.search(u'category:CategorySearchTestNotExisting')
        assert not result.hits

    def test_category_search_re(self):
        result = self.search(ur'category:re:\bCategoryHomepage\b')
        assert len(result.hits) == 1

        result = self.search(ur'category:re:\bCategoryHomepa\b')
        assert not result.hits

    def test_category_search_case(self):
        result = self.search(u'category:case:CategoryHomepage')
        assert len(result.hits) == 1

        result = self.search(u'category:case:categoryhomepage')
        assert not result.hits

    def test_category_search_case_re(self):
        result = self.search(ur'category:case:re:\bCategoryHomepage\b')
        assert len(result.hits) == 1

        result = self.search(ur'category:case:re:\bcategoryhomepage\b')
        assert not result.hits

    def test_mimetype_search_simple(self):
        result = self.search(u'mimetype:text/wiki')
        assert len(result.hits) == 10

    def test_mimetype_search_re(self):
        result = self.search(ur'mimetype:re:\btext/wiki\b')
        assert len(result.hits) == 10

        result = self.search(ur'category:re:\bCategoryHomepa\b')
        assert not result.hits

    def test_language_search_simple(self):
        result = self.search(u'language:en')
        assert len(result.hits) == 10

    def test_domain_search_simple(self):
        result = self.search(u'domain:system')
        assert result.hits

    def test_search_and(self):
        """ search: title search with AND expression """
        result = self.search(u"title:HelpOnCreoleSyntax lang:en")
        assert len(result.hits) == 1

        result = self.search(u"title:HelpOnCreoleSyntax lang:de")
        assert len(result.hits) == 0

        result = self.search(u"title:Help title:%s" % self.doesnotexist)
        assert not result.hits

    def testTitleSearchOR(self):
        """ search: title search with OR expression """
        result = self.search(u"title:FrontPage or title:RecentChanges")
        assert len(result.hits) == 2

    def testTitleSearchNegatedFindAll(self):
        """ search: negated title search for some pagename that does not exist results in all pagenames """
        result = self.search(u"-title:%s" % self.doesnotexist)
        assert len(result.hits) == len(self.pages)

    def testTitleSearchNegativeTerm(self):
        """ search: title search for a AND expression with a negative term """
        result = self.search(u"-title:FrontPage")
        assert len(result.hits) == len(self.pages) - 1

    def testFullSearchNegatedFindAll(self):
        """ search: negated full search for some string that does not exist results in all pages """
        result = self.search(u"-%s" % self.doesnotexist)
        assert len(result.hits) == len(self.pages)

    def test_title_search(self):
        query = QueryParser(titlesearch=True).parse_query('FrontPage')
        result = self.search(query)
        assert len(result.hits) == 1

    def test_create_page(self):
        self.pages['TestCreatePage'] = 'some text' # Moin serarch must search this page
        create_page(self.request, 'TestCreatePage', self.pages['TestCreatePage'])

        time.sleep(1) # Wait while created pages are being indexed in other thread.
        result = self.search(u'TestCreatePage')

        nuke_page(self.request, 'TestCreatePage')
        time.sleep(1) # Wait while the xapian index is being updated.
        del self.pages['TestCreatePage']

        assert len(result.hits) == 1


class TestMoinSearch(BaseSearchTest):

    def get_searcher(self, query):
        pages = [{'pagename': page, 'attachment': '', 'wikiname': 'Self', } for page in self.pages]
        return MoinSearch(self.request, query, pages=pages)


class TestXapianSearch(BaseSearchTest):
    """ search: test Xapian indexing """

    class Config(wikiconfig.Config):

        xapian_search = True

    def get_searcher(self, query):
        return XapianSearch(self.request, query)

    def get_moin_search_connection(self):
        from MoinMoin.search.Xapian import MoinSearchConnection
        return  MoinSearchConnection(os.path.join(self.request.cfg.cache_dir, 'xapian/index'))

    def setup_method(self, method):

        try:
            from MoinMoin.search.Xapian import Index
        except ImportError:
            py.test.skip('xapian is not installed')

        nuke_xapian_index(self.request)
        index = Index(self.request)
        index.indexPages(mode='add', pages=self.pages)

    def teardown_method(self, method):
        nuke_xapian_index(self.request)

    def test_get_all_documents(self):
        connection = self.get_moin_search_connection()
        documents = connection.get_all_documents()

        assert len(self.pages) == len(documents)
        for document in documents:
            assert document.data['pagename'][0] in self.pages.keys()

    def test_xapian_term(self):
        parser = QueryParser()
        connection = self.get_moin_search_connection()

        prefixes = {u'': ([u'', u're:', u'case:', u'case:re:'], u'SearchTestPage'),
                    u'title:': ([u'', u're:', u'case:', u'case:re:'], u'SearchTestPage'),
                    u'linkto:': ([u'', u're:', u'case:', u'case:re:'], u'FrontPage'),
                    u'category:': ([u'', u're:', u'case:', u'case:re:'], u'CategoryHomepage'),
                    u'mimetype:': ([u'', u're:'], u'text/wiki'),
                    u'language:': ([u''], u'en'),
                    u'domain:': ([u''], u'system')}

        def test_query(query):
            assert not parser.parse_query(query).xapian_term(self.request, connection).empty()

        for prefix, data in prefixes.iteritems():
            modifiers, term = data
            for modifier in modifiers:
                query = ''.join([prefix, modifier, term])
                yield query, test_query, query


class TestXapianIndexingInNewThread(object):
    """ search: test Xapian indexing """

    class Config(wikiconfig.Config):

        xapian_search = True

    def test_index_in_new_thread(self):
        """ search: kicks off indexing for a single pages in Xapian """
        try:
            from MoinMoin.search.Xapian import Index
        except ImportError:
            py.test.skip('xapian is not installed')

        nuke_xapian_index(self.request)
        index = Index(self.request)
        index.indexPagesInNewThread(mode='add')

        nuke_xapian_index(self.request)


coverage_modules = ['MoinMoin.search']

