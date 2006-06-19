# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - search engine
    
    @copyright: 2005 MoinMoin:FlorianFesti,
                2005 MoinMoin:NirSoffer,
                2005 MoinMoin:AlexanderSchremmer,
                2006 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
    @license: GNU GPL, see COPYING for details
"""

import re, time, sys, StringIO, string, operator
from sets import Set
from MoinMoin import wikiutil, config
from MoinMoin.Page import Page

try:
    import Xapian
    from Xapian import Query, UnicodeQuery
    use_stemming = Xapian.use_stemming
except ImportError:
    use_stemming = False

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

    def xapian_term(self, request):
        # sort negated terms
        terms = []
        not_terms = []
        for term in self._subterms:
            if not term.negated:
                terms.append(term.xapian_term(request))
            else:
                not_terms.append(term.xapian_term(request))

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

    def xapian_term(self, request):
        # XXX: negated terms managed by _moinSearch?
        return Query(Query.OP_OR, [term.xapian_term(request) for term in self._subterms])


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
            if use_stemming:
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
            # XXX why not return None or empty list?
            return [Match()]

    def xapian_wanted(self):
        return not self.use_re

    def xapian_term(self, request):
        if self.use_re:
            return None # xapian can't do regex search
        else:
            analyzer = Xapian.WikiAnalyzer(language=request.cfg.language_default)
            terms = self._pattern.split()

            # all parsed wikiwords, AND'ed
            queries = []
            stemmed = []
            for t in terms:
                if use_stemming:
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
                    (self.titlesearch.xapian_term(request),
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
            if use_stemming:
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
            # XXX why not return None or empty list?
            return [Match()]

    def xapian_wanted(self):
        return not self.use_re

    def xapian_term(self, request):
        if self.use_re:
            return None # xapian doesn't support regex search
        else:
            analyzer = Xapian.WikiAnalyzer(language=request.cfg.language_default)
            terms = self._pattern.split()
            terms = [list(analyzer.raw_tokenize(t)) for t in terms]

            # all parsed wikiwords, AND'ed
            queries = []
            stemmed = []
            for t in terms:
                if use_stemming:
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
        try:
            if not use_re:
                raise re.error
            self.search_re = re.compile(pattern, flags)
            self.static = False
        except re.error:
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
            # XXX why not return None or empty list?
            return [Match()]

    def xapian_wanted(self):
        return not self.use_re

    def xapian_term(self, request):
        pattern = self.pattern
        if self.use_re:
            return None # xapian doesnt support regex search
        else:
            return UnicodeQuery('%s:%s' %
                    (Xapian.Index.prefixMap['linkto'], pattern))


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
            return None
        else:
            # XXX why not return None or empty list?
            return [Match()]

    def xapian_wanted(self):
        return not self.use_re

    def xapian_term(self, request):
        pattern = self.pattern
        if self.use_re:
            return None # xapian doesnt support regex search
        else:
            self.xapian_called = True
            return UnicodeQuery('%s%s' %
                    (Xapian.Index.prefixMap['lang'], pattern))


############################################################################
### Results
############################################################################

class Match(object):
    """ Base class for all Matches (found pieces of pages).
    
    This class represents a empty True value as returned from negated searches.
    """
    # Default match weight
    _weight = 1.0
    
    def __init__(self, start=0, end=0, re_match=None):
        self.re_match = re_match
        if not re_match:
            self._start = start
            self._end = end
        else:
            self._start = self._end = 0

    def __len__(self):
        return self.end - self.start

    def __eq__(self, other):
        equal = (self.__class__ == other.__class__ and
                 self.start == other.start and
                 self.end == other.end)
        return equal
        
    def __ne__(self, other):
        return not self.__eq__(other)

    def view(self):
        return ''

    def weight(self):
        return self._weight

    def _get_start(self):
        if self.re_match:
            return self.re_match.start()
        return self._start

    def _get_end(self):
        if self.re_match:
            return self.re_match.end()
        return self._end

    # object properties
    start = property(_get_start)
    end   = property(_get_end)


class TextMatch(Match):
    """ Represents a match in the page content """
    pass


class TitleMatch(Match):
    """ Represents a match in the page title
    
    Has more weight as a match in the page content.
    """
    # Matches in titles are much more important in wikis. This setting
    # seems to make all pages that have matches in the title to appear
    # before pages that their title does not match.
    _weight = 100.0


class AttachmentMatch(Match):
    """ Represents a match in a attachment content

    Not used yet.
    """
    pass


class FoundPage:
    """ Represents a page in a search result """

    def __init__(self, page_name, matches=None, page=None):
        self.page_name = page_name
        self.attachment = '' # this is not an attachment
        self.page = page
        if matches is None:
            matches = []
        self._matches = matches

    def weight(self, unique=1):
        """ returns how important this page is for the terms searched for

        Summarize the weight of all page matches

        @param unique: ignore identical matches
        @rtype: int
        @return: page weight
        """
        weight = 0
        for match in self.get_matches(unique=unique):
            weight += match.weight()
            # More sophisticated things to be added, like increase
            # weight of near matches.
        return weight

    def add_matches(self, matches):
        """ Add found matches """
        self._matches.extend(matches)

    def get_matches(self, unique=1, sort='start', type=Match):
        """ Return all matches of type sorted by sort

        @param unique: return only unique matches (bool)
        @param sort: match attribute to sort by (string)
        @param type: type of match to return (Match or sub class) 
        @rtype: list
        @return: list of matches
        """
        if unique:
            matches = self._unique_matches(type=type)
            if sort == 'start':
                # matches already sorted by match.start, finished.
                return matches
        else:
            matches = self._matches

        # Filter by type and sort by sort using fast schwartzian
        # transform.
        if sort == 'start':
            tmp = [(match.start, match) for match in matches
                   if instance(match, type)]
        else:
            tmp = [(match.weight(), match) for match in matches
                   if instance(match, type)]
        tmp.sort()
        if sort == 'weight':
            tmp.reverse()
        matches = [item[1] for item in tmp]
        
        return matches

    def _unique_matches(self, type=Match):
        """ Get a list of unique matches of type

        The result is sorted by match.start, because its easy to remove
        duplicates like this.

        @param type: type of match to return
        @rtype: list
        @return: list of matches of type, sorted by match.start
        """
        # Filter by type and sort by match.start using fast schwartzian
        # transform.
        tmp = [(match.start, match) for match in self._matches
               if isinstance(match, type)]
        tmp.sort()

        if not len(tmp):
            return []

        # Get first match into matches list
        matches = [tmp[0][1]]

        # Add the remaining ones of matches ignoring identical matches
        for item in tmp[1:]:
            if item[1] == matches[-1]:
                continue
            matches.append(item[1])

        return matches
    

class FoundAttachment(FoundPage):
    """ Represent an attachment in search results """
    
    def __init__(self, page_name, attachment, matches=None, page=None):
        self.page_name = page_name
        self.attachment = attachment
        self.page = page
        if matches is None:
            matches = []
        self._matches = matches

    def weight(self, unique=1):
        return 1

    def get_matches(self, unique=1, sort='start', type=Match):
        return []

    def _unique_matches(self, type=Match):
        return []


class FoundRemote(FoundPage):
    """ Represent an attachment in search results """
    
    def __init__(self, wikiname, page_name, attachment, matches=None, page=None):
        self.wikiname = wikiname
        self.page_name = page_name
        self.attachment = attachment
        self.page = page
        if matches is None:
            matches = []
        self._matches = matches

    def weight(self, unique=1):
        return 1

    def get_matches(self, unique=1, sort='start', type=Match):
        return []

    def _unique_matches(self, type=Match):
        return []


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


############################################################################
### Search results formatting
############################################################################

class SearchResults:
    """ Manage search results, supply different views

    Search results can hold valid search results and format them for
    many requests, until the wiki content changes.

    For example, one might ask for full page list sorted from A to Z,
    and then ask for the same list sorted from Z to A. Or sort results
    by name and then by rank.
    """
    # Public functions --------------------------------------------------
    
    def __init__(self, query, hits, pages, elapsed):
        self.query = query # the query
        self.hits = hits # hits list
        self.sort = None # hits are unsorted initially
        self.pages = pages # number of pages in the wiki
        self.elapsed = elapsed # search time

    def sortByWeight(self):
        """ Sorts found pages by the weight of the matches """
        tmp = [(hit.weight(), hit.page_name, hit) for hit in self.hits]
        tmp.sort()
        tmp.reverse()
        self.hits = [item[2] for item in tmp]
        self.sort = 'weight'
        
    def sortByPagename(self):
        """ Sorts a list of found pages alphabetical by page name """
        tmp = [(hit.page_name, hit) for hit in self.hits]
        tmp.sort()
        self.hits = [item[1] for item in tmp]
        self.sort = 'page_name'
        
    def stats(self, request, formatter):
        """ Return search statistics, formatted with formatter

        @param request: current request
        @param formatter: formatter to use
        @rtype: unicode
        @return formatted statistics
        """
        _ = request.getText
        output = [
            formatter.paragraph(1),
            formatter.text(_("%(hits)d results out of about %(pages)d pages.") %
                   {'hits': len(self.hits), 'pages': self.pages}),
            u' (%s)' % formatter.text(_("%.2f seconds") % self.elapsed),
            formatter.paragraph(0),
            ]
        return ''.join(output)

    def pageList(self, request, formatter, info=0, numbered=1):
        """ Format a list of found pages

        @param request: current request
        @param formatter: formatter to use
        @param info: show match info in title
        @param numbered: use numbered list for display
        @rtype: unicode
        @return formatted page list
        """
        self._reset(request, formatter)
        f = formatter
        write = self.buffer.write
        if numbered:
            list = f.number_list
        else:
            list = f.bullet_list

        # Add pages formatted as list
        if self.hits:
            write(list(1))

            for page in self.hits:
                if page.attachment:
                    querydict = {
                        'action': 'AttachFile',
                        'do': 'get',
                        'target': page.attachment,
                    }
                else:
                    querydict = None
                querystr = self.querystring(querydict)
            
                matchInfo = ''
                if info:
                    matchInfo = self.formatInfo(f, page)
                item = [
                    f.listitem(1),
                    f.pagelink(1, page.page_name, querystr=querystr),
                    self.formatTitle(page),
                    f.pagelink(0, page.page_name),
                    matchInfo,
                    f.listitem(0),
                    ]
                write(''.join(item))
            write(list(0))

        return self.getvalue()

    def pageListWithContext(self, request, formatter, info=1, context=180,
                            maxlines=1):
        """ Format a list of found pages with context

        The default parameter values will create Google-like search
        results, as this is the most known search interface. Good
        interface is familiar interface, so unless we have much better
        solution (we don't), being like Google is the way.

        @param request: current request
        @param formatter: formatter to use
        @param info: show match info near the page link
        @param context: how many characters to show around each match. 
        @param maxlines: how many contexts lines to show. 
        @rtype: unicode
        @return formatted page list with context
        """
        self._reset(request, formatter)
        f = formatter
        write = self.buffer.write
        
        # Add pages formatted as definition list
        if self.hits:
            write(f.definition_list(1))       

            for page in self.hits:
                matchInfo = ''
                if info:
                    matchInfo = self.formatInfo(f, page)
                if page.attachment:
                    fmt_context = ""
                    querydict = {
                        'action': 'AttachFile',
                        'do': 'get',
                        'target': page.attachment,
                    }
                else:
                    fmt_context = self.formatContext(page, context, maxlines)
                    querydict = None
                querystr = self.querystring(querydict)
                item = [
                    f.definition_term(1),
                    f.pagelink(1, page.page_name, querystr=querystr),
                    self.formatTitle(page),
                    f.pagelink(0, page.page_name),
                    matchInfo,
                    f.definition_term(0),
                    f.definition_desc(1),
                    fmt_context,
                    f.definition_desc(0),
                    ]
                write(''.join(item))
            write(f.definition_list(0))
        
        return self.getvalue()

    # Private -----------------------------------------------------------

    # This methods are not meant to be used by clients and may change
    # without notice.
    
    def formatContext(self, page, context, maxlines):
        """ Format search context for each matched page

        Try to show first maxlines interesting matches context.
        """
        f = self.formatter
        if not page.page:
            page.page = Page(self.request, page.page_name)
        body = page.page.get_raw_body()
        last = len(body) - 1
        lineCount = 0
        output = []
        
        # Get unique text matches sorted by match.start, try to ignore
        # matches in page header, and show the first maxlines matches.
        # TODO: when we implement weight algorithm for text matches, we
        # should get the list of text matches sorted by weight and show
        # the first maxlines matches.
        matches = page.get_matches(unique=1, sort='start', type=TextMatch)
        i, start = self.firstInterestingMatch(page, matches)            

        # Format context
        while i < len(matches) and lineCount < maxlines:
            match = matches[i]
            
            # Get context range for this match
            start, end = self.contextRange(context, match, start, last)

            # Format context lines for matches. Each complete match in
            # the context will be highlighted, and if the full match is
            # in the context, we increase the index, and will not show
            # same match again on a separate line.

            output.append(f.text(u'...'))
            
            # Get the index of the first match completely within the
            # context.
            for j in xrange(0, len(matches)):
                if matches[j].start >= start:
                    break

            # Add all matches in context and the text between them 
            while True:
                match = matches[j]
                # Ignore matches behind the current position
                if start < match.end:
                    # Append the text before match
                    if start < match.start:
                        output.append(f.text(body[start:match.start]))
                    # And the match
                    output.append(self.formatMatch(body, match, start))
                    start = match.end
                # Get next match, but only if its completely within the context
                if j < len(matches) - 1 and matches[j + 1].end <= end:
                    j += 1
                else:
                    break

            # Add text after last match and finish the line
            if match.end < end:
               output.append(f.text(body[match.end:end]))
            output.append(f.text(u'...'))
            output.append(f.linebreak(preformatted=0))

            # Increase line and point to the next match
            lineCount += 1
            i = j + 1

        output = ''.join(output)

        if not output:
            # Return the first context characters from the page text
            output = f.text(page.page.getPageText(length=context))
            output = output.strip()
            if not output:
                # This is a page with no text, only header, for example,
                # a redirect page.
                output = f.text(page.page.getPageHeader(length=context))
        
        return output
        
    def firstInterestingMatch(self, page, matches):
        """ Return the first interesting match

        This function is needed only because we don't have yet a weight
        algorithm for page text matches.
        
        Try to find the first match in the page text. If we can't find
        one, we return the first match and start=0.

        @rtype: tuple
        @return: index of first match, start of text
        """
        header = page.page.getPageHeader()
        start = len(header)
        # Find first match after start
        for i in xrange(len(matches)):
            if matches[i].start >= start:
                return i, start
        return 0, 0

    def contextRange(self, context, match, start, last):
        """ Compute context range

        Add context around each match. If there is no room for context
        before or after the match, show more context on the other side.

        @param context: context length
        @param match: current match
        @param start: context should not start before that index, unless
                      end is past the last character.
        @param last: last character index
        @rtype: tuple
        @return: start, end of context
        """
        # Start by giving equal context on both sides of match
        contextlen = max(context - len(match), 0)
        cstart = match.start - contextlen / 2
        cend = match.end + contextlen / 2

        # If context start before start, give more context on end
        if cstart < start:
            cend += start - cstart
            cstart = start
            
        # But if end if after last, give back context to start
        if cend > last:
            cstart -= cend - last
            cend = last

        # Keep context start positive for very short texts
        cstart = max(cstart, 0)

        return cstart, cend

    def formatTitle(self, page):
        """ Format page title

        Invoke format match on all unique matches in page title.

        @param page: found page
        @rtype: unicode
        @return: formatted title
        """
        # Get unique title matches sorted by match.start
        matches = page.get_matches(unique=1, sort='start', type=TitleMatch)
        
        # Format
        pagename = page.page_name
        f = self.formatter
        output = []
        start = 0
        for match in matches:
            # Ignore matches behind the current position
            if start < match.end:
                # Append the text before the match
                if start < match.start:
                    output.append(f.text(pagename[start:match.start]))
                # And the match
                output.append(self.formatMatch(pagename, match, start))
                start = match.end
        # Add text after match
        if start < len(pagename):
            output.append(f.text(pagename[start:]))
        
        if page.attachment: # show the attachment that matched
            output.extend([
                    " ",
                    f.strong(1),
                    f.text("(%s)" % page.attachment),
                    f.strong(0)])

        return ''.join(output)

    def formatMatch(self, body, match, location):
        """ Format single match in text

        Format the part of the match after the current location in the
        text. Matches behind location are ignored and an empty string is
        returned.

        @param body: text containing match
        @param match: search match in text
        @param location: current location in text
        @rtype: unicode
        @return: formatted match or empty string
        """        
        start = max(location, match.start)
        if start < match.end:
            f = self.formatter
            output = [
                f.strong(1),
                f.text(body[start:match.end]),
                f.strong(0),
                ]
            return ''.join(output)
        return ''

    def querystring(self, querydict=None):
        """ Return query string, used in the page link """
        if querydict is None:
            querydict = {'highlight': self.query.highlight_re()}
        querystr = wikiutil.makeQueryString(querydict)
        #querystr = wikiutil.escape(querystr)
        return querystr

    def formatInfo(self, formatter, page):
        """ Return formatted match info """
        template = u' . . . %s %s'
        template = u"%s%s%s" % (formatter.span(1, css_class="info"),
                                template,
                                formatter.span(0))
        # Count number of unique matches in text of all types
        count = len(page.get_matches(unique=1))
        info = template % (count, self.matchLabel[count != 1])
        return info

    def getvalue(self):
        """ Return output in div with CSS class """
        write = self.request.write
        value = [
            self.formatter.div(1, css_class='searchresults'),
            self.buffer.getvalue(),
            self.formatter.div(0),
            ]
        return '\n'.join(value)

    def _reset(self, request, formatter):
        """ Update internal state before new output

        Do not call this, it should be called only by the instance code.

        Each request might need different translations or other user
        preferences.
        """
        self.buffer = StringIO.StringIO()
        self.formatter = formatter
        self.request = request
        # Use 1 match, 2 matches...
        _ = request.getText    
        self.matchLabel = (_('match'), _('matches'))


##############################################################################
### Searching
##############################################################################

class Search:
    """ A search run """
    
    def __init__(self, request, query):
        self.request = request
        self.query = query
        self.filtered = False
        self.fs_rootpage = "FS" # XXX FS hardcoded

    def run(self):
        """ Perform search and return results object """
        start = time.time()
        if self.request.cfg.xapian_search:
            hits = self._xapianSearch()
        else:
            hits = self._moinSearch()
            
        # important - filter deleted pages or pages the user may not read!
        if not self.filtered:
            hits = self._filter(hits)
        
        result_hits = []
        for wikiname, page, attachment, match in hits:
            if wikiname in (self.request.cfg.interwikiname, 'Self'): # a local match
                if attachment:
                    result_hits.append(FoundAttachment(page.page_name, attachment))
                else:
                    result_hits.append(FoundPage(page.page_name, match))
            else:
                result_hits.append(FoundRemote(wikiname, page, attachment, match))
        elapsed = time.time() - start
        count = self.request.rootpage.getPageCount()
        return SearchResults(self.query, result_hits, count, elapsed)

    # ----------------------------------------------------------------
    # Private!

    def _xapianSearch(self):
        """ Search using Xapian
        
        Get a list of pages using fast xapian search and
        return moin search in those pages.
        """
        pages = None
        try:
            index = Xapian.Index(self.request)
        except NameError:
            index = None
        if index and index.exists() and self.query.xapian_wanted():
            self.request.clock.start('_xapianSearch')
            try:
                from MoinMoin.support import xapwrap
                query = self.query.xapian_term(self.request)
                self.request.log("xapianSearch: query = %r" %
                        query.get_description())
                query = xapwrap.index.QObjQuery(query)
                hits = index.search(query)
                self.request.log("xapianSearch: finds: %r" % hits)
                def dict_decode(d):
                    """ decode dict values to unicode """
                    for k, v in d.items():
                        d[k] = d[k].decode(config.charset)
                    return d
                pages = [dict_decode(hit['values']) for hit in hits]
                self.request.log("xapianSearch: finds pages: %r" % pages)
            except index.LockedException:
                pass
            self.request.clock.stop('_xapianSearch')
        return self._moinSearch(pages)

    def _moinSearch(self, pages=None):
        """ Search pages using moin's built-in full text search 
        
        Return list of tuples (page, match). The list may contain
        deleted pages or pages the user may not read.
        """
        self.request.clock.start('_moinSearch')
        from MoinMoin.Page import Page
        if pages is None:
            # if we are not called from _xapianSearch, we make a full pagelist,
            # but don't search attachments (thus attachment name = '')
            pages = [{'pagename': p, 'attachment': '', 'wikiname': 'Self', } for p in self._getPageList()]
        hits = []
        fs_rootpage = self.fs_rootpage
        for valuedict in pages:
            wikiname = valuedict['wikiname']
            pagename = valuedict['pagename']
            attachment = valuedict['attachment']
            if wikiname in (self.request.cfg.interwikiname, 'Self'): # THIS wiki
                page = Page(self.request, pagename)
                if attachment:
                    if pagename == fs_rootpage: # not really an attachment
                        page = Page(self.request, "%s%s" % (fs_rootpage, attachment))
                        hits.append((wikiname, page, None, None))
                    else:
                        hits.append((wikiname, page, attachment, None))
                else:
                    match = self.query.search(page)
                    if match:
                        hits.append((wikiname, page, attachment, match))
            else: # other wiki
                hits.append((wikiname, pagename, attachment, None))
        self.request.clock.stop('_moinSearch')
        return hits

    def _getPageList(self):
        """ Get list of pages to search in 
        
        If the query has a page filter, use it to filter pages before
        searching. If not, get a unfiltered page list. The filtering
        will happen later on the hits, which is faster with current
        slow storage.
        """
        filter = self.query.pageFilter()
        if filter:
            # There is no need to filter the results again.
            self.filtered = True
            return self.request.rootpage.getPageList(filter=filter)
        else:
            return self.request.rootpage.getPageList(user='', exists=0)
        
    def _filter(self, hits):
        """ Filter out deleted or acl protected pages """
        userMayRead = self.request.user.may.read
        fs_rootpage = self.fs_rootpage + "/"
        thiswiki = (self.request.cfg.interwikiname, 'Self')
        filtered = [(wikiname, page, attachment, match) for wikiname, page, attachment, match in hits
                    if not wikiname in thiswiki or
                       page.exists() and userMayRead(page.page_name) or
                       page.page_name.startswith(fs_rootpage)]    
        return filtered
        
        
def searchPages(request, query, **kw):
    """ Search the text of all pages for query.
    
    @param request: current request
    @param query: the expression we want to search for
    @rtype: SearchResults instance
    @return: search results
    """
    return Search(request, query).run()

