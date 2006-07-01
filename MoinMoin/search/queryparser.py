# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - search engine query parser
    
    @copyright: 2005 MoinMoin:FlorianFesti,
                2005 MoinMoin:NirSoffer,
                2005 MoinMoin:AlexanderSchremmer,
                2006 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
    @license: GNU GPL, see COPYING for details
"""

import re, string
from MoinMoin import config
from MoinMoin.search.results import Match, TitleMatch, TextMatch

try:
    from MoinMoin.search import Xapian
    from MoinMoin.search.Xapian import Query, UnicodeQuery
except ImportError:
    pass

#############################################################################
### query objects
#############################################################################

class BaseExpression:
    """ Base class for all search terms """
    
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
            # XXX why?
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
        return ''

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
            result += self.operator + t
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
                """ A function that return True if all terms filter name """
                for term in terms:
                    filter = term.pageFilter()
                    if not filter(name):
                        return False
                return True
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
            if highlight_re: result.append(highlight_re)
            
        return '|'.join(result)

    def xapian_wanted(self):
        wanted = True
        for term in self._subterms:
            wanted = wanted and term.xapian_wanted()
        return wanted

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
        if len(terms) == 1:
            t1 = Query(terms[0])
        else:
            t1 = Query(Query.OP_AND, terms)

        # negated terms?
        if not not_terms:
            # no, just return query for not negated terms
            return t1
        
        # yes, link not negated and negated terms' query with a AND_NOT query
        if len(not_terms) == 1:
            t2 = Query(not_terms[0])
        else:
            t2 = Query(Query.OP_OR, not_terms)

        return Query(Query.OP_AND_NOT, t1, t2)


class OrExpression(AndExpression):
    """ A term connecting several sub terms with a logical OR """
    
    operator = ' or '

    def search(self, page):
        """ Search page with terms, cheap terms first

        XXX Do we have any reason to sort here? we are not breaking out
        of the search in any case.
        """
        self.sortByCost()
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
        
    def costs(self):
        return 10000
    
    def __unicode__(self):
        neg = self.negated and '-' or ''
        return u'%s"%s"' % (neg, unicode(self._pattern))

    def highlight_re(self):
        return u"(%s)" % self._pattern

    def search(self, page):
        matches = []

        # Search in page name
        results = self.titlesearch.search(page)
        if results:
            matches.extend(results)

        # Search in page body
        body = page.get_raw_body()
        for match in self.search_re.finditer(body):
            if page.request.cfg.xapian_stemming:
                # somewhere in regular word
                if body[match.start()] not in config.chars_upper and \
                        body[match.start()-1] in config.chars_lower:
                    continue

                post = 0
                for c in body[match.end():]:
                    if c in config.chars_lower:
                        post += 1
                    else:
                        break

                matches.append(TextMatch(start=match.start(),
                        end=match.end()+post))
            else:
                matches.append(TextMatch(re_match=match))

        # Decide what to do with the results.
        if ((self.negated and matches) or
            (not self.negated and not matches)):
            return None
        elif matches:
            return matches
        else:
            return []

    def xapian_wanted(self):
        return not self.use_re

    def xapian_term(self, request, allterms):
        if self.use_re:
            # basic regex matching per term
            terms = [term for term in allterms() if
                    self.search_re.match(term)]
            if not terms:
                return None
            queries = [Query(Query.OP_OR, terms)]
        else:
            analyzer = Xapian.WikiAnalyzer(request=request,
                    language=request.cfg.language_default)
            terms = self._pattern.split()

            # all parsed wikiwords, AND'ed
            queries = []
            stemmed = []
            for t in terms:
                if request.cfg.xapian_stemming:
                    # stemmed OR not stemmed
                    tmp = []
                    for i in analyzer.tokenize(t, flat_stemming=False):
                        tmp.append(UnicodeQuery(Query.OP_OR, i))
                        stemmed.append(i[1])
                    t = tmp
                else:
                    # just not stemmed
                    t = [UnicodeQuery(i) for i in analyzer.tokenize(t)]
                queries.append(Query(Query.OP_AND, t))

            if stemmed:
                self._build_re(' '.join(stemmed), use_re=False,
                        case=self.case, stemmed=True)

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
        
    def costs(self):
        return 100

    def __unicode__(self):
        neg = self.negated and '-' or ''
        return u'%s!"%s"' % (neg, unicode(self._pattern))

    def highlight_re(self):
        return u"(%s)" % self._pattern

    def pageFilter(self):
        """ Page filter function for single title search """
        def filter(name):
            match = self.search_re.search(name)
            if ((self.negated and match) or
                (not self.negated and not match)):
                return False
            return True
        return filter
            
    def search(self, page):
        # Get matches in page name
        matches = []
        for match in self.search_re.finditer(page.page_name):
            if page.request.cfg.xapian_stemming:
                # somewhere in regular word
                if page.page_name[match.start()] not in config.chars_upper and \
                        page.page_name[match.start()-1] in config.chars_lower:
                    continue

                post = 0
                for c in page.page_name[match.end():]:
                    if c in config.chars_lower:
                        post += 1
                    else:
                        break

                matches.append(TitleMatch(start=match.start(),
                        end=match.end()+post))
            else:
                matches.append(TitleMatch(re_match=match))
        
        if ((self.negated and matches) or
            (not self.negated and not matches)):
            return None
        elif matches:
            return matches
        else:
            return []

    def xapian_wanted(self):
        return not self.use_re

    def xapian_term(self, request, allterms):
        if self.use_re:
            # basic regex matching per term
            terms = [term for term in allterms() if
                    self.search_re.match(term)]
            if not terms:
                return None
            queries = [Query(Query.OP_OR, terms)]
        else:
            analyzer = Xapian.WikiAnalyzer(request=request,
                    language=request.cfg.language_default)
            terms = self._pattern.split()
            terms = [list(analyzer.raw_tokenize(t)) for t in terms]

            # all parsed wikiwords, AND'ed
            queries = []
            stemmed = []
            for t in terms:
                if request.cfg.xapian_stemming:
                    # stemmed OR not stemmed
                    tmp = []
                    for i in analyzer.tokenize(t, flat_stemming=False):
                        tmp.append(UnicodeQuery(Query.OP_OR, ['%s%s' %
                            (Xapian.Index.prefixMap['title'], j) for j in i]))
                        stemmed.append(i[1])
                    t = tmp
                else:
                    # just not stemmed
                    t = [UnicodeQuery('%s%s' % (Xapian.Index.prefixMap['title'], i))
                        for i in analyzer.tokenize(t)]

                queries.append(Query(Query.OP_AND, t))

            if stemmed:
                self._build_re(' '.join(stemmed), use_re=False,
                        case=self.case, stemmed=True)

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

    def _build_re(self, pattern, use_re=False, case=False):
        """ Make a regular expression out of a text pattern """
        flags = case and re.U or (re.I | re.U)
        if use_re:
            self.search_re = re.compile(pattern, flags)
            self.static = False
        else:
            self.pattern = pattern
            self.static = True
        
    def costs(self):
        return 5000 # cheaper than a TextSearch

    def __unicode__(self):
        neg = self.negated and '-' or ''
        return u'%s!"%s"' % (neg, unicode(self._pattern))

    def highlight_re(self):
        return u"(%s)" % self._textpattern

    def search(self, page):
        # Get matches in page name
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
            else: #This happens e.g. for pages that use navigation macros
                matches.append(TextMatch(0, 0))

        # Decide what to do with the results.
        if ((self.negated and matches) or
            (not self.negated and not matches)):
            return None
        elif matches:
            return matches
        else:
            return []

    def xapian_wanted(self):
        return not self.use_re

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
                return None
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
        self.case = case
        self.xapian_called = False
        self._build_re(self._pattern, use_re=use_re, case=case)

    def costs(self):
        return 5000 # cheaper than a TextSearch

    def __unicode__(self):
        neg = self.negated and '-' or ''
        return u'%s!"%s"' % (neg, unicode(self._pattern))

    def highlight_re(self):
        return ""

    def search(self, page):
        # We just use (and trust ;)) xapian for this.. deactivated for _moinSearch
        if not self.xapian_called:
            return []
        else:
            return [Match()]

    def xapian_wanted(self):
        return not self.use_re

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
                return None
            return Query(Query.OP_OR, terms)
        else:
            pattern = self.pattern
            return UnicodeQuery('%s%s' % (prefix, pattern))


##############################################################################
### Parse Query
##############################################################################

class QueryParser:
    """
    Converts a String into a tree of Query objects
    using recursive top/down parsing
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

    def parse_query(self, query):
        """ transform an string into a tree of Query objects """
        if isinstance(query, str):
            query = query.decode(config.charset)
        self._query = query
        result = self._or_expression()
        if result is None:
            result = BaseExpression()
        return result

    def _or_expression(self):
        result = self._and_expression()
        if self._query:
            result = OrExpression(result)
        while self._query:
            q = self._and_expression()
            if q:
                result.append(q)
        return result
            
    def _and_expression(self):
        result = None
        while not result and self._query:
            result = self._single_term()
        term = self._single_term()
        if term:
            result = AndExpression(result, term)
        else:
            return result
        term = self._single_term()
        while term:
            result.append(term)
            term = self._single_term()
        return result
                                
    def _single_term(self):
        regex = (r'(?P<NEG>-?)\s*(' +              # leading '-'
                 r'(?P<OPS>\(|\)|(or\b(?!$)))|' +  # or, (, )
                 r'(?P<MOD>(\w+:)*)' +
                 r'(?P<TERM>("[^"]+")|' +
                 r"('[^']+')|(\S+)))")             # search word itself
        self._query = self._query.strip()
        match = re.match(regex, self._query, re.U)
        if not match:
            return None
        self._query = self._query[match.end():]
        ops = match.group("OPS")
        if ops == '(':
            result = self._or_expression()
            if match.group("NEG"): result.negate()
            return result
        elif ops == ')':
            return None
        elif ops == 'or':
            return None
        modifiers = match.group('MOD').split(":")[:-1]
        text = match.group('TERM')
        if self.isQuoted(text):
            text = text[1:-1]

        title_search = self.titlesearch
        regex = self.regex
        case = self.case
        linkto = False
        lang = False

        for m in modifiers:
            if "title".startswith(m):
                title_search = True
            elif "regex".startswith(m):
                regex = True
            elif "case".startswith(m):
                case = True
            elif "linkto".startswith(m):
                linkto = True
            elif "language".startswith(m):
                lang = True

        if lang:
            obj = LanguageSearch(text, use_re=regex, case=False)
        elif linkto:
            obj = LinkSearch(text, use_re=regex, case=case)
        elif title_search:
            obj = TitleSearch(text, use_re=regex, case=case)
        else:
            obj = TextSearch(text, use_re=regex, case=case)

        if match.group("NEG"):
            obj.negate()
        return obj

    def isQuoted(self, text):
        # Empty string '' is not considered quoted
        if len(text) < 3:
            return False
        return (text.startswith('"') and text.endswith('"') or
                text.startswith("'") and text.endswith("'"))



