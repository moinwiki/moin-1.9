# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - search query parser

    @copyright: 2005 MoinMoin:FlorianFesti,
                2005 MoinMoin:NirSoffer,
                2005 MoinMoin:AlexanderSchremmer,
                2006-2008 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
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

class QueryError(ValueError):
    """ error raised for problems when parsing the query """


#############################################################################
### query objects
#############################################################################

class BaseExpression:
    """ Base class for all search terms """

    _tag = ""

    def __init__(self):
        self.negated = 0

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

    def search(self, page):
        """ Search a page

        Returns a list of Match objects or None if term didn't find
        anything (vice versa if negate() was called).  Terms containing
        other terms must call this method to aggregate the results.
        This Base class returns True (Match()) if not negated.
        """
        if self.negated:
            return [Match()]
        else:
            return None

    def costs(self):
        """ Return estimated time to calculate this term

        Number is relative to other terms and has no real unit.
        It allows to do the fast searches first.
        """
        return 0

    def highlight_re(self):
        """ Return a regular expression of what the term searches for

        Used to display the needle in the page.
        """
        return u''

    def _build_re(self, pattern, use_re=False, case=False, stemmed=False):
        """ Make a regular expression out of a text pattern """
        flags = case and re.U or (re.I | re.U)
        if use_re:
            try:
                self.search_re = re.compile(pattern, flags)
            except re.error:
                pattern = re.escape(pattern)
                self.pattern = pattern
                self.search_re = re.compile(pattern, flags)
            else:
                self.pattern = pattern
        else:
            pattern = re.escape(pattern)
            self.search_re = re.compile(pattern, flags)
            self.pattern = pattern

    def xapian_wanted(self):
        return False

    def __unicode__(self):
        neg = self.negated and '-' or ''
        return u'%s%s"%s"' % (neg, self._tag, unicode(self._pattern))


class AndExpression(BaseExpression):
    """ A term connecting several sub terms with a logical AND """

    operator = ' '

    def __init__(self, *terms):
        self._subterms = list(terms)
        self._costs = 0
        for t in self._subterms:
            self._costs += t.costs()
        self.negated = 0

    def append(self, expression):
        """ Append another term """
        self._subterms.append(expression)
        self._costs += expression.costs()

    def subterms(self):
        return self._subterms

    def costs(self):
        return self._costs

    def __unicode__(self):
        result = ''
        for t in self._subterms:
            result += self.operator + unicode(t)
        return u'[' + result[len(self.operator):] + u']'

    def pageFilter(self):
        """ Return a page filtering function

        This function is used to filter page list before we search it.

        Return a function that gets a page name, and return bool, or None.
        """
        # Sort terms by cost, then get all title searches
        self.sortByCost()
        terms = [term for term in self._subterms if isinstance(term, TitleSearch)]
        if terms:
            # Create and return a filter function
            def filter(name):
                """ A function that returns True if all terms filter name """
                result = None
                for term in terms:
                    _filter = term.pageFilter()
                    t = _filter(name)
                    if t is False:
                        result = False
                        break
                    elif t is True:
                        result = True
                logging.debug("pageFilter AND returns %r" % result)
                return result
            return filter

        return None

    def sortByCost(self):
        tmp = [(term.costs(), term) for term in self._subterms]
        tmp.sort()
        self._subterms = [item[1] for item in tmp]

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

    def xapian_wanted(self):
        wanted = True
        for term in self._subterms:
            wanted = wanted and term.xapian_wanted()
        return wanted

    def xapian_need_postproc(self):
        for term in self._subterms:
            if term.xapian_need_postproc():
                return True
        return False

    def xapian_term(self, request, allterms):
        # sort negated terms
        terms = []
        not_terms = []
        for term in self._subterms:
            if not term.negated:
                terms.append(term.xapian_term(request, allterms))
            else:
                not_terms.append(term.xapian_term(request, allterms))

        # prepare query for not negated terms
        if not terms:
            t1 = None
        elif len(terms) == 1:
            t1 = Query(terms[0])
        else:
            t1 = Query(Query.OP_AND, terms)

        # prepare query for negated terms
        if not not_terms:
            t2 = None
        elif len(not_terms) == 1:
            t2 = Query(not_terms[0])
        else:
            t2 = Query(Query.OP_OR, not_terms)

        if t1 and not t2:
            return t1
        elif t2 and not t1:
            return Query(Query.OP_AND_NOT, Query(""), t2)  # Query("") == MatchAll
        else:
            # yes, link not negated and negated terms' query with a AND_NOT query
            return Query(Query.OP_AND_NOT, t1, t2)


class OrExpression(AndExpression):
    """ A term connecting several sub terms with a logical OR """

    operator = ' or '

    def pageFilter(self):
        """ Return a page filtering function

        This function is used to filter page list before we search it.

        Return a function that gets a page name, and return bool, or None.
        """
        # Sort terms by cost, then get all title searches
        self.sortByCost()
        terms = [term for term in self._subterms if isinstance(term, TitleSearch)]
        if terms:
            # Create and return a filter function
            def filter(name):
                """ A function that returns True if any term filters name """
                result = None
                for term in terms:
                    _filter = term.pageFilter()
                    t = _filter(name)
                    if t is True:
                        return True
                    elif t is False:
                        result = False
                logging.debug("pageFilter OR returns %r" % result)
                return result
            return filter

        return None

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

    def xapian_term(self, request, allterms):
        # XXX: negated terms managed by _moinSearch?
        return Query(Query.OP_OR, [term.xapian_term(request, allterms) for term in self._subterms])


class TextSearch(BaseExpression):
    """ A term that does a normal text search

    Both page content and the page title are searched, using an
    additional TitleSearch term.
    """

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
        self._build_re(self._pattern, use_re=use_re, case=case)
        self.titlesearch = TitleSearch(self._pattern, use_re=use_re, case=case)
        self._tag = ''
        if use_re:
            self._tag += 're:'
        if case:
            self._tag += 'case:'

    def costs(self):
        return 10000

    def highlight_re(self):
        return u"(%s)" % self.pattern

    def search(self, page):
        logging.debug("TextSearch searching page %r for (negated = %r) %r" % (page.page_name, self.negated, self._pattern))
        matches = []

        # Search in page name
        if self.titlesearch:
            results = self.titlesearch.search(page)
            if results:
                matches.extend(results)

        # Search in page body
        body = page.get_raw_body()
        for match in self.search_re.finditer(body):
            matches.append(TextMatch(re_match=match))

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
        logging.debug("TextSearch returning %r" % result)
        return result

    def xapian_wanted(self):
        # XXX: Add option for term-based matching
        return not self.use_re

    def xapian_need_postproc(self):
        return self.case

    def xapian_term(self, request, allterms):
        if self.use_re:
            # basic regex matching per term
            terms = [term for term in allterms() if self.search_re.match(term)]
            if not terms:
                return Query()
            queries = [Query(Query.OP_OR, terms)]
        else:
            analyzer = Xapian.WikiAnalyzer(request=request, language=request.cfg.language_default)
            terms = self._pattern.split()

            # all parsed wikiwords, AND'ed
            queries = []
            stemmed = []
            for t in terms:
                if request.cfg.xapian_stemming:
                    # stemmed OR not stemmed
                    tmp = []
                    for w, s, pos in analyzer.tokenize(t, flat_stemming=False):
                        tmp.append(UnicodeQuery(Query.OP_OR, (w, s)))
                        stemmed.append(s)
                    t = tmp
                else:
                    # just not stemmed
                    t = [UnicodeQuery(w) for w, pos in analyzer.tokenize(t)]
                queries.append(Query(Query.OP_AND, t))

            if not self.case and stemmed:
                new_pat = ' '.join(stemmed)
                self._pattern = new_pat
                self._build_re(new_pat, use_re=False, case=self.case, stemmed=True)

        # titlesearch OR parsed wikiwords
        return Query(Query.OP_OR,
                (self.titlesearch.xapian_term(request, allterms),
                    Query(Query.OP_AND, queries)))


class TitleSearch(BaseExpression):
    """ Term searches in pattern in page title only """

    def __init__(self, pattern, use_re=False, case=False):
        """ Init a title search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        self._pattern = unicode(pattern)
        self.negated = 0
        self.use_re = use_re
        self.case = case
        self._build_re(self._pattern, use_re=use_re, case=case)

        self._tag = 'title:'
        if use_re:
            self._tag += 're:'
        if case:
            self._tag += 'case:'

    def costs(self):
        return 100

    def highlight_re(self):
        return u'' # do not highlight text with stuff from titlesearch,
                   # was: return u"(%s)" % self._pattern

    def pageFilter(self):
        """ Page filter function for single title search """
        def filter(name):
            match = self.search_re.search(name)
            result = bool(self.negated) ^ bool(match)
            logging.debug("pageFilter title returns %r (%r)" % (result, self.pattern))
            return result
        return filter

    def search(self, page):
        """ Get matches in page name """
        logging.debug("TitleSearch searching page %r for (negated = %r) %r" % (page.page_name, self.negated, self._pattern))
        matches = []
        for match in self.search_re.finditer(page.page_name):
            matches.append(TitleMatch(re_match=match))

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
        logging.debug("TitleSearch returning %r" % result)
        return result

    def xapian_wanted(self):
        return True # only easy regexps possible

    def xapian_need_postproc(self):
        return self.case

    def xapian_term(self, request, allterms):
        if self.use_re:
            # basic regex matching per term
            terms = []
            found = False
            for term in allterms():
                if term[:4] == 'XFT:':
                    found = True
                    if self.search_re.findall(term[4:]):
                        terms.append(Query(term, 100))
                elif found:
                    break
            if not terms:
                return Query()
            queries = [Query(Query.OP_OR, terms)]
        else:
            analyzer = Xapian.WikiAnalyzer(request=request,
                    language=request.cfg.language_default)
            terms = self._pattern.split()
            terms = [[w for w, pos in analyzer.raw_tokenize(t)] for t in terms]

            # all parsed wikiwords, ANDed
            queries = []
            stemmed = []
            for t in terms:
                if request.cfg.xapian_stemming:
                    # stemmed OR not stemmed
                    tmp = []
                    for w, s, pos in analyzer.tokenize(t, flat_stemming=False):
                        tmp.append(Query(Query.OP_OR,
                            [UnicodeQuery('%s%s' %
                                    (Xapian.Index.prefixMap['title'], j),
                                    100)
                                for j in (w, s)]))
                        stemmed.append(s)
                    t = tmp
                else:
                    # just not stemmed
                    t = [UnicodeQuery(
                                '%s%s' % (Xapian.Index.prefixMap['title'], w),
                                100)
                            for w, pos in analyzer.tokenize(t)]

                queries.append(Query(Query.OP_AND, t))

            if not self.case and stemmed:
                new_pat = ' '.join(stemmed)
                self._pattern = new_pat
                self._build_re(new_pat, use_re=False, case=self.case, stemmed=True)

        return Query(Query.OP_AND, queries)


class LinkSearch(BaseExpression):
    """ Search the term in the pagelinks """

    def __init__(self, pattern, use_re=False, case=True):
        """ Init a link search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        # used for search in links
        self._pattern = pattern
        # used for search in text
        self._textpattern = '(' + self._pattern.replace('/', '|') + ')'
        self.negated = 0
        self.use_re = use_re
        self.case = case
        self.textsearch = TextSearch(self._textpattern, use_re=1, case=case)
        self._build_re(unicode(pattern), use_re=use_re, case=case)

        self._tag = 'linkto:'
        if use_re:
            self._tag += 're:'
        if case:
            self._tag += 'case:'

    def _build_re(self, pattern, use_re=False, case=False):
        """ Make a regular expression out of a text pattern """
        flags = case and re.U or (re.I | re.U)
        if use_re:
            self.search_re = re.compile(pattern, flags)
            self.pattern = pattern
            self.static = False
        else:
            self.pattern = pattern
            self.static = True

    def costs(self):
        return 5000 # cheaper than a TextSearch

    def highlight_re(self):
        return u"(%s)" % self._textpattern

    def search(self, page):
        # Get matches in page links
        logging.debug("LinkSearch searching page %r for (negated = %r) %r" % (page.page_name, self.negated, self._pattern))
        matches = []
        Found = True

        for link in page.getPageLinks(page.request):
            if ((self.static and self.pattern == link) or
                (not self.static and self.search_re.match(link))):
                break
        else:
            Found = False

        if Found:
            # Search in page text
            results = self.textsearch.search(page)
            if results:
                matches.extend(results)
            else: # This happens e.g. for pages that use navigation macros
                matches.append(TextMatch(0, 0))

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
        logging.debug("LinkSearch returning %r" % result)
        return result

    def xapian_wanted(self):
        return True # only easy regexps possible

    def xapian_need_postproc(self):
        return self.case

    def xapian_term(self, request, allterms):
        prefix = Xapian.Index.prefixMap['linkto']
        if self.use_re:
            # basic regex matching per term
            terms = []
            found = None
            n = len(prefix)
            for term in allterms():
                if prefix == term[:n]:
                    found = True
                    if self.search_re.match(term[n+1:]):
                        terms.append(term)
                elif found:
                    continue

            if not terms:
                return Query()
            return Query(Query.OP_OR, terms)
        else:
            return UnicodeQuery('%s:%s' % (prefix, self.pattern))


class LanguageSearch(BaseExpression):
    """ Search the pages written in a language """

    def __init__(self, pattern, use_re=False, case=True):
        """ Init a language search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        # iso language code, always lowercase
        self._pattern = pattern.lower()
        self.negated = 0
        self.use_re = use_re
        self.case = False       # not case-sensitive!
        self.xapian_called = False
        self._build_re(self._pattern, use_re=use_re, case=case)

        self._tag = 'language:'
        if use_re:
            self._tag += 're:'
        if case:
            self._tag += 'case:'

    def costs(self):
        return 5000 # cheaper than a TextSearch

    def highlight_re(self):
        return u""

    def search(self, page):
        logging.debug("LanguageSearch searching page %r for (negated = %r) %r" % (page.page_name, self.negated, self._pattern))
        match = False
        body = page.getPageHeader()

        comma = re.compile(',')
        iterator = comma.finditer(self.pattern)
        temp = 0
        for m_obj in iterator:
            if re.findall('#language %s' % self.pattern[temp:m_obj.end()-2], body):
                match = True
            temp = m_obj.end()

        # Decide what to do with the results.
        if self.negated:
            if match:
                result = None
            else:
                result = [Match()] # represents "matched" (but as it was a negative match, we have nothing to show)
        else: # not negated
            if match:
                result = [Match()] # represents "matched" (but we have nothing to show)
            else:
                result = None
        logging.debug("LanguageSearch returning %r" % result)
        return result

    def xapian_wanted(self):
        return True # only easy regexps possible

    def xapian_need_postproc(self):
        return False # case-sensitivity would make no sense

    def xapian_term(self, request, allterms):
        self.xapian_called = True
        prefix = Xapian.Index.prefixMap['lang']
        if self.use_re:
            # basic regex matching per term
            terms = []
            found = None
            n = len(prefix)
            for term in allterms():
                if prefix == term[:n]:
                    found = True
                    if self.search_re.match(term[n:]):
                        terms.append(term)
                elif found:
                    continue

            if not terms:
                return Query()
            return Query(Query.OP_OR, terms)
        else:
            pattern = self.pattern
            return UnicodeQuery('%s%s' % (prefix, pattern))


class CategorySearch(TextSearch):
    """ Search the pages belonging to a category """

    def __init__(self, *args, **kwargs):
        TextSearch.__init__(self, *args, **kwargs)
        self.titlesearch = None

        self._tag = 'category:'

    def _build_re(self, pattern, **kwargs):
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
        kwargs['use_re'] = True
        TextSearch._build_re(self,
                r'(?m)(^-----*\s*\r?\n)(^##.*\r?\n)*^(?!##)(.*)\b%s\b' % pattern, **kwargs)

    def costs(self):
        return 5000 # cheaper than a TextSearch

    def highlight_re(self):
        return u'(\\b%s\\b)' % self._pattern

    def xapian_wanted(self):
        return True # only easy regexps possible

    def xapian_need_postproc(self):
        return self.case

    def xapian_term(self, request, allterms):
        self.xapian_called = True
        prefix = Xapian.Index.prefixMap['category']
        if self.use_re:
            # basic regex matching per term
            terms = []
            found = None
            n = len(prefix)
            for term in allterms():
                if prefix == term[:n]:
                    found = True
                    if self.search_re.match(term[n+1:]):
                        terms.append(term)
                elif found:
                    continue

            if not terms:
                return Query()
            return Query(Query.OP_OR, terms)
        else:
            pattern = self._pattern.lower()
            return UnicodeQuery('%s:%s' % (prefix, pattern))


class MimetypeSearch(BaseExpression):
    """ Search for files belonging to a specific mimetype """

    def __init__(self, pattern, use_re=False, case=True):
        """ Init a mimetype search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        self._pattern = pattern.lower()
        self.negated = 0
        self.use_re = use_re
        self.case = False # not case-sensitive!
        self.xapian_called = False
        self._build_re(self._pattern, use_re=use_re, case=case)

        self._tag = 'mimetype:'
        if use_re:
            self._tag += 're:'
        if case:
            self._tag += 'case:'

    def costs(self):
        return 5000 # cheaper than a TextSearch

    def highlight_re(self):
        return u""

    def search(self, page):
        page_mimetype = u'text/%s' % page.pi['format']
        matches = self.search_re.search(page_mimetype)
        if matches and not self.negated or not matches and self.negated:
            return [Match()]
        else:
            return None

    def xapian_wanted(self):
        return True # only easy regexps possible

    def xapian_need_postproc(self):
        return False # case-sensitivity would make no sense

    def xapian_term(self, request, allterms):
        self.xapian_called = True
        prefix = Xapian.Index.prefixMap['mimetype']
        if self.use_re:
            # basic regex matching per term
            terms = []
            found = None
            n = len(prefix)
            for term in allterms():
                if prefix == term[:n]:
                    found = True
                    if self.search_re.match(term[n:]):
                        terms.append(term)
                elif found:
                    continue

            if not terms:
                return Query()
            return Query(Query.OP_OR, terms)
        else:
            pattern = self._pattern
            return UnicodeQuery('%s%s' % (prefix, pattern))


class DomainSearch(BaseExpression):
    """ Search for pages belonging to a specific domain """

    def __init__(self, pattern, use_re=False, case=True):
        """ Init a domain search

        @param pattern: pattern to search for, ascii string or unicode
        @param use_re: treat pattern as re of plain text, bool
        @param case: do case sensitive search, bool
        """
        self._pattern = pattern.lower()
        self.negated = 0
        self.use_re = use_re
        self.case = False # not case-sensitive!
        self.xapian_called = False
        self._build_re(self._pattern, use_re=use_re, case=case)

        self._tag = 'domain:'
        if use_re:
            self._tag += 're:'
        if case:
            self._tag += 'case:'

    def costs(self):
        return 5000 # cheaper than a TextSearch

    def highlight_re(self):
        return u""

    def search(self, page):
        logging.debug("DomainSearch searching page %r for (negated = %r) %r" % (page.page_name, self.negated, self._pattern))
        checks = {'underlay': page.isUnderlayPage,
                  'standard': page.isStandardPage,
                  'system': lambda page=page: wikiutil.isSystemPage(page.request, page.page_name),
                 }

        try:
            match = checks[self.pattern]()
        except KeyError:
            match = False

        # Decide what to do with the results.
        if self.negated:
            if match:
                result = None
            else:
                result = [Match()] # represents "matched" (but as it was a negative match, we have nothing to show)
        else: # not negated
            if match:
                result = [Match()] # represents "matched" (but we have nothing to show)
            else:
                result = None
        logging.debug("DomainSearch returning %r" % result)
        return result

    def xapian_wanted(self):
        return True # only easy regexps possible

    def xapian_need_postproc(self):
        return False # case-sensitivity would make no sense

    def xapian_term(self, request, allterms):
        self.xapian_called = True
        prefix = Xapian.Index.prefixMap['domain']
        if self.use_re:
            # basic regex matching per term
            terms = []
            found = None
            n = len(prefix)
            for term in allterms():
                if prefix == term[:n]:
                    found = True
                    if self.search_re.match(term[n+1:]):
                        terms.append(term)
                elif found:
                    continue

            if not terms:
                return Query()
            return Query(Query.OP_OR, terms)
        else:
            pattern = self._pattern
            return UnicodeQuery('%s:%s' % (prefix, pattern))


##############################################################################
### Parse Query
##############################################################################

class QueryParser:
    """
    Converts a String into a tree of Query objects.
    """

    def __init__(self, **kw):
        """
        @keyword titlesearch: treat all terms as title searches
        @keyword case: do case sensitive search
        @keyword regex: treat all terms as regular expressions
        """
        self.titlesearch = kw.get('titlesearch', 0)
        self.case = kw.get('case', 0)
        self.regex = kw.get('regex', 0)
        self._M = wikiutil.ParserPrefix('-')

    def _analyse_items(self, items):
        terms = AndExpression()
        M = self._M
        while items:
            item = items[0]
            items = items[1:]

            if isinstance(item, unicode):
                if item.lower() == 'or':
                    sub = terms.subterms()
                    if len(sub) >= 1:
                        last = sub[-1]
                        if last.__class__ == OrExpression:
                            orexpr = last
                        else:
                            # Note: do NOT reduce "terms" when it has a single subterm only!
                            # Doing that would break "-someterm" searches as we rely on AndExpression
                            # doing a "MatchAll AND_NOT someterm" for that case!
                            orexpr = OrExpression(terms)
                        terms = AndExpression(orexpr)
                    else:
                        raise QueryError('Nothing to OR')
                    remaining = self._analyse_items(items)
                    if remaining.__class__ == OrExpression:
                        for sub in remaining.subterms():
                            orexpr.append(sub)
                    else:
                        orexpr.append(remaining)
                    break
                elif item.lower() == 'and':
                    pass
                else:
                    # odd workaround; we should instead ignore this term
                    # and reject expressions that contain nothing after
                    # being parsed rather than rejecting an empty string
                    # before parsing...
                    if not item:
                        raise QueryError("Term too short")
                    regex = self.regex
                    case = self.case
                    if self.titlesearch:
                        terms.append(TitleSearch(item, use_re=regex, case=case))
                    else:
                        terms.append(TextSearch(item, use_re=regex, case=case))
            elif isinstance(item, tuple):
                negate = item[0] == M
                title_search = self.titlesearch
                regex = self.regex
                case = self.case
                linkto = False
                lang = False
                category = False
                mimetype = False
                domain = False
                while len(item) > 1:
                    m = item[0]
                    if m is None:
                        raise QueryError("Invalid search prefix")
                    elif m == M:
                        negate = True
                    elif "title".startswith(m):
                        title_search = True
                    elif "regex".startswith(m):
                        regex = True
                    elif "case".startswith(m):
                        case = True
                    elif "linkto".startswith(m):
                        linkto = True
                    elif "language".startswith(m):
                        lang = True
                    elif "category".startswith(m):
                        category = True
                    elif "mimetype".startswith(m):
                        mimetype = True
                    elif "domain".startswith(m):
                        domain = True
                    else:
                        raise QueryError("Invalid search prefix")
                    item = item[1:]

                text = item[0]
                if category:
                    obj = CategorySearch(text, use_re=regex, case=case)
                elif mimetype:
                    obj = MimetypeSearch(text, use_re=regex, case=False)
                elif lang:
                    obj = LanguageSearch(text, use_re=regex, case=False)
                elif linkto:
                    obj = LinkSearch(text, use_re=regex, case=case)
                elif domain:
                    obj = DomainSearch(text, use_re=regex, case=False)
                elif title_search:
                    obj = TitleSearch(text, use_re=regex, case=case)
                else:
                    obj = TextSearch(text, use_re=regex, case=case)
                obj.negated = negate
                terms.append(obj)
            elif isinstance(item, list):
                # strip off the opening parenthesis
                terms.append(self._analyse_items(item[1:]))

        # Note: do NOT reduce "terms" when it has a single subterm only!
        # Doing that would break "-someterm" searches as we rely on AndExpression
        # doing a "MatchAll AND_NOT someterm" for that case!
        return terms

    def parse_query(self, query):
        """ transform an string into a tree of Query objects """
        if isinstance(query, str):
            query = query.decode(config.charset)
        try:
            items = wikiutil.parse_quoted_separated_ext(query,
                                                        name_value_separator=':',
                                                        prefixes='-',
                                                        multikey=True,
                                                        brackets=('()', ),
                                                        quotes='\'"')
        except wikiutil.BracketError, err:
            raise QueryError(str(err))
        logging.debug("parse_quoted_separated items: %r" % items)
        query = self._analyse_items(items)
        logging.debug("analyse_items query: %r" % query)
        return query
