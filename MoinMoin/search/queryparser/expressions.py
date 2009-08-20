# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - search query expressions

    @copyright: 2005 MoinMoin:FlorianFesti,
                2005 MoinMoin:NirSoffer,
                2005 MoinMoin:AlexanderSchremmer,
                2006-2008 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz,
                2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details
"""

import re

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, wikiutil
from MoinMoin.search.results import Match, TitleMatch, TextMatch

try:
    from MoinMoin.search import Xapian
    from MoinMoin.search.Xapian import Query, UnicodeQuery
except ImportError:
    pass


class BaseExpression(object):
    """ Base class for all search terms """

    # costs is estimated time to calculate this term.
    # Number is relative to other terms and has no real unit.
    # It allows to do the fast searches first.
    costs = 0
    _tag = ""

    def __init__(self, pattern, use_re=False, case=False):
        """ Init a text search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        self._pattern = unicode(pattern)
        self.negated = 0
        self.use_re = use_re
        self.case = case

        if use_re:
            self._tag += 're:'
        if case:
            self._tag += 'case:'

        self.pattern, self.search_re = self._build_re(self._pattern, use_re=use_re, case=case)

    def __str__(self):
        return unicode(self).encode(config.charset, 'replace')

    def negate(self):
        """ Negate the result of this term """
        self.negated = 1

    def pageFilter(self):
        """ Return a page filtering function

        This function is used to filter page list before we search
        it. Return a function that get a page name, and return bool.

        The default expression does not have any filter function and
        return None. Sub class may define custom filter functions.
        """
        return None

    def _get_matches(self, page):
        raise NotImplementedError

    def search(self, page):
        """ Search a page

        Returns a list of Match objects or None if term didn't find
        anything (vice versa if negate() was called).  Terms containing
        other terms must call this method to aggregate the results.
        This Base class returns True (Match()) if not negated.
        """
        logging.debug("%s searching page %r for (negated = %r) %r" % (self.__class__, page.page_name, self.negated, self._pattern))

        matches = self._get_matches(page)

        # Decide what to do with the results.
        if self.negated:
            if matches:
                result = None
            else:
                result = [Match()] # represents "matched" (but as it was a negative match, we have nothing to show)
        else: # not negated
            if matches:
                result = matches
            else:
                result = None
        logging.debug("%s returning %r" % (self.__class__, result))
        return result

    def highlight_re(self):
        """ Return a regular expression of what the term searches for

        Used to display the needle in the page.
        """
        return u''

    def _build_re(self, pattern, use_re=False, case=False, stemmed=False):
        """ Make a regular expression out of a text pattern """
        flags = case and re.U or (re.I | re.U)

        try:
            search_re = re.compile(pattern, flags)
        except re.error:
            pattern = re.escape(pattern)
            search_re = re.compile(pattern, flags)

        return pattern, search_re

    def _get_query_for_search_re(self, connection, field_to_check=None):
        """
        Return a query which satisfy self.search_re for field values.
        If field_to_check is given check values only for that field.
        """
        queries = []

        documents = connection.get_all_documents()
        for document in documents:
            data = document.data
            if field_to_check:
                # Check only field with given name
                if field_to_check in data:
                    for term in data[field_to_check]:
                        if self.search_re.match(term):
                            queries.append(connection.query_field(field_to_check, term))
            else:
                # Check all fields
                for field, terms in data.iteritems():
                    for term in terms:
                        if self.search_re.match(term):
                            queries.append(connection.query_field(field_to_check, term))

        return Query(Query.OP_OR, queries)

    def xapian_need_postproc(self):
        return self.case

    def __unicode__(self):
        neg = self.negated and '-' or ''
        return u'%s%s"%s"' % (neg, self._tag, unicode(self._pattern))


class AndExpression(BaseExpression):
    """ A term connecting several sub terms with a logical AND """

    operator = ' '

    def __init__(self, *terms):
        self._subterms = list(terms)
        self.negated = 0

    def append(self, expression):
        """ Append another term """
        self._subterms.append(expression)

    def subterms(self):
        return self._subterms

    @property
    def costs(self):
        return sum([t.costs for t in self._subterms])

    def __unicode__(self):
        result = ''
        for t in self._subterms:
            result += self.operator + unicode(t)
        return u'[' + result[len(self.operator):] + u']'

    def _filter(self, terms, name):
        """ A function that returns True if all terms filter name """
        result = None
        for term in terms:
            _filter = term.pageFilter()
            t = _filter(name)
            if t is True:
                result = True
            elif t is False:
                result = False
                break
        logging.debug("pageFilter AND returns %r" % result)
        return result

    def pageFilter(self):
        """ Return a page filtering function

        This function is used to filter page list before we search it.

        Return a function that gets a page name, and return bool, or None.
        """
        # Sort terms by cost, then get all title searches
        self.sortByCost()
        terms = [term for term in self._subterms if isinstance(term, TitleSearch)]
        if terms:
            return lambda name: self._filter(terms, name)

    def sortByCost(self):
        self._subterms.sort(key=lambda t: t.costs)

    def search(self, page):
        """ Search for each term, cheap searches first """
        self.sortByCost()
        matches = []
        for term in self._subterms:
            result = term.search(page)
            if not result:
                return None
            matches.extend(result)
        return matches

    def highlight_re(self):
        result = []
        for s in self._subterms:
            highlight_re = s.highlight_re()
            if highlight_re:
                result.append(highlight_re)

        return u'|'.join(result)

    def xapian_need_postproc(self):
        for term in self._subterms:
            if term.xapian_need_postproc():
                return True
        return False

    def xapian_term(self, request, connection):
        # sort negated terms
        terms = []
        not_terms = []

        for term in self._subterms:
            if not term.negated:
                terms.append(term.xapian_term(request, connection))
            else:
                not_terms.append(term.xapian_term(request, connection))

        # prepare query for not negated terms
        if terms:
            query = Query(Query.OP_AND, terms)
        else:
            query = Query('') # MatchAll

        # prepare query for negated terms
        if not_terms:
            query_negated = Query(Query.OP_OR, not_terms)
        else:
            query_negated = Query()

        return Query(Query.OP_AND_NOT, query, query_negated)


class OrExpression(AndExpression):
    """ A term connecting several sub terms with a logical OR """

    operator = ' or '

    def _filter(self, terms, name):
        """ A function that returns True if any term filters name """
        result = None
        for term in terms:
            _filter = term.pageFilter()
            t = _filter(name)
            if t is True:
                result = True
                break
            elif t is False:
                result = False
        logging.debug("pageFilter OR returns %r" % result)
        return result

    def search(self, page):
        """ Search page with terms

        @param page: the page instance
        """

        # XXX Do we have any reason to sort here? we are not breaking out
        # of the search in any case.
        #self.sortByCost()
        matches = []
        for term in self._subterms:
            result = term.search(page)
            if result:
                matches.extend(result)
        return matches

    def xapian_term(self, request, connection):
        # XXX: negated terms managed by _moinSearch?
        return Query(Query.OP_OR, [term.xapian_term(request, connection) for term in self._subterms])


class TextSearch(BaseExpression):
    """ A term that does a normal text search

    Both page content and the page title are searched, using an
    additional TitleSearch term.
    """

    costs = 10000

    def highlight_re(self):
        return u"(%s)" % self.pattern

    def _get_matches(self, page):
        matches = []

        # Search in page name
        results = TitleSearch(self._pattern, use_re=self.use_re, case=self.case)._get_matches(page)
        if results:
            matches.extend(results)

        # Search in page body
        body = page.get_raw_body()
        for match in self.search_re.finditer(body):
            matches.append(TextMatch(re_match=match))

        return matches

    def xapian_term(self, request, connection):
        # XXX next version of xappy (>0.5) will provide Query class
        # it should be used.
        if self.use_re:
            queries = [self._get_query_for_search_re(connection)]
        else:
            analyzer = Xapian.WikiAnalyzer(request=request, language=request.cfg.language_default)
            terms = self._pattern.split()

            # all parsed wikiwords, AND'ed
            queries = []
            stemmed = []

            for term in terms:
                if request.cfg.xapian_stemming:
                    # stemmed OR not stemmed
                    t = []
                    for w, s, pos in analyzer.tokenize(term, flat_stemming=False):
                        query_word = connection.query_field('content', w)
                        query_stemmed = connection.query_field('content', s)
                        # XXX UnicodeQuery was used here!
                        t.append(Query(Query.OP_OR, [query_word, query_stemmed]))
                        stemmed.append(s)
                else:
                    # just not stemmed
                    t = [connection.query_field('content', w) for w, pos in analyzer.tokenize(term)]

                queries.append(Query(connection.OP_AND, t))

            # XXX Is it required to change pattern and search_re here?
            if not self.case and stemmed:
                new_pat = ' '.join(stemmed)
                self._pattern = new_pat
                self.pattern, self.search_re = self._build_re(new_pat, use_re=False, case=self.case, stemmed=True)

        title_query = TitleSearch(self._pattern, use_re=self.use_re, case=self.case).xapian_term(request, connection)
        return Query(Query.OP_OR, [title_query, Query(Query.OP_AND, queries)])


class TitleSearch(BaseExpression):
    """ Term searches in pattern in page title only """

    _tag = 'title:'
    costs = 100

    def pageFilter(self):
        """ Page filter function for single title search """
        def filter(name):
            match = self.search_re.search(name)
            result = bool(self.negated) ^ bool(match)
            logging.debug("pageFilter title returns %r (%r)" % (result, self.pattern))
            return result
        return filter

    def _get_matches(self, page):
        """ Get matches in page name """
        matches = []

        for match in self.search_re.finditer(page.page_name):
            matches.append(TitleMatch(re_match=match))

        return matches

    def xapian_term(self, request, connection):
        if self.use_re:
            # XXX weight for a query!
            queries = [self._get_query_for_search_re(connection, 'fulltitle')]
        else:
            analyzer = Xapian.WikiAnalyzer(request=request,
                    language=request.cfg.language_default)
            terms = self._pattern.split()
            terms = [[w for w, pos in analyzer.raw_tokenize(t)] for t in terms]

            # all parsed wikiwords, ANDed
            queries = []
            stemmed = []
            for term in terms:
                if request.cfg.xapian_stemming:
                    # stemmed OR not stemmed
                    t = []
                    for w, s, pos in analyzer.tokenize(term, flat_stemming=False):
                        # XXX weight for a query 100!
                        query_word = connection.query_field('title', w)
                        query_stemmed = connection.query_field('title', s)

                        # XXX UnicodeQuery was used here!
                        t.append(Query(Query.OP_OR, [query_word, query_stemmed]))
                        stemmed.append(s)
                else:
                    # just not stemmed
                    # XXX weight for a query 100!
                    # XXX UnicodeQuery was used here!
                    t = [connection.query_field('title', w) for w, pos in analyzer.tokenize(term)]

                # XXX what should be there OR or AND?!
                queries.append(Query(Query.OP_OR, t))

            if not self.case and stemmed:
                new_pat = ' '.join(stemmed)
                self._pattern = new_pat
                self._build_re(new_pat, use_re=False, case=self.case, stemmed=True)

        return Query(Query.OP_AND, queries)


class BaseFieldSearch(BaseExpression):

    _field_to_search = None

    def xapian_term(self, request, connection):
        if self.use_re:
            return self._get_query_for_search_re(connection, self._field_to_search)
        else:
            return connection.query_field(self._field_to_search, self._pattern)


class LinkSearch(BaseFieldSearch):
    """ Search the term in the pagelinks """

    _tag = 'linkto:'
    _field_to_search = 'linkto'
    costs = 5000 # cheaper than a TextSearch

    def __init__(self, pattern, use_re=False, case=True):
        """ Init a link search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """

        super(LinkSearch, self).__init__(pattern, use_re, case)

        self._textpattern = '(' + pattern.replace('/', '|') + ')' # used for search in text
        self.textsearch = TextSearch(self._textpattern, use_re=True, case=case)

    def highlight_re(self):
        return u"(%s)" % self._textpattern

    def _get_matches(self, page):
        # Get matches in page links
        matches = []

        # XXX in python 2.5 any() may be used.
        found = False
        for link in page.getPageLinks(page.request):
            if self.search_re.match(link):
                found = True
                break

        if found:
            # Search in page text
            results = self.textsearch.search(page)
            if results:
                matches.extend(results)
            else: # This happens e.g. for pages that use navigation macros
                matches.append(TextMatch(0, 0))

        return matches


class LanguageSearch(BaseFieldSearch):
    """ Search the pages written in a language """

    _tag = 'language:'
    _field_to_search = 'lang'
    costs = 5000 # cheaper than a TextSearch

    def __init__(self, pattern, use_re=False, case=False):
        """ Init a language search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        # iso language code, always lowercase and not case-sensitive
        super(LanguageSearch, self).__init__(pattern.lower(), use_re, case=False)

    def _get_matches(self, page):

        if self.pattern == page.pi['language']:
            return [Match()]
        else:
            return []


class CategorySearch(BaseFieldSearch):
    """ Search the pages belonging to a category """

    _tag = 'category:'
    _field_to_search = 'category'
    costs = 5000 # cheaper than a TextSearch

    def _get_matches(self, page):
        """ match categories like this:
            ... some page text ...
            ----
            ## optionally some comments, e.g. about possible categories:
            ## CategoryFoo
            CategoryTheRealAndOnly

            Note: there might be multiple comment lines, but all real categories
                  must be on a single line either directly below the ---- or
                  directly below some comment lines.
        """
        matches = []

        pattern = r'(?m)(^-----*\s*\r?\n)(^##.*\r?\n)*^(?!##)(.*)\b%s\b' % self.pattern
        search_re = self._build_re(pattern, use_re=self.use_re, case=self.case)[1] # we need only a regexp, but not a pattern

        body = page.get_raw_body()
        for match in search_re.finditer(body):
            matches.append(TextMatch(re_match=match))

        return matches

    def highlight_re(self):
        return u'(\\b%s\\b)' % self._pattern

    def xapian_term(self, request, connection):
        # XXX Probably, it is a good idea to inherit this class from
        # BaseFieldSearch and get rid of this definition
        if self.use_re:
            return self._get_query_for_search_re(connection, 'category')
        else:
            pattern = self._pattern
            # XXX UnicodeQuery was used
            return connection.query_field('category', pattern)


class MimetypeSearch(BaseFieldSearch):
    """ Search for files belonging to a specific mimetype """

    _tag = 'mimetype:'
    _field_to_search = 'mimetype'
    costs = 5000 # cheaper than a TextSearch

    def __init__(self, pattern, use_re=False, case=False):
        """ Init a mimetype search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        # always lowercase and not case-sensitive
        super(MimetypeSearch, self).__init__(pattern.lower(), use_re, case=False)

    def _get_matches(self, page):

        page_mimetype = u'text/%s' % page.pi['format']

        if self.search_re.search(page_mimetype):
            return [Match()]
        else:
            return []


class DomainSearch(BaseFieldSearch):
    """ Search for pages belonging to a specific domain """

    _tag = 'domain:'
    _field_to_search = 'domain'
    costs = 5000 # cheaper than a TextSearch

    def __init__(self, pattern, use_re=False, case=False):
        """ Init a domain search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        # always lowercase and not case-sensitive
        super(DomainSearch, self).__init__(pattern.lower(), use_re, case=False)

    def _get_matches(self, page):
        checks = {'underlay': page.isUnderlayPage,
                  'standard': page.isStandardPage,
                  'system': lambda page=page: wikiutil.isSystemPage(page.request, page.page_name),
                 }

        try:
            match = checks[self.pattern]()
        except KeyError:
            match = False

        if match:
            return [Match()]
        else:
            return []

