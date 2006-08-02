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

import StringIO, time, re
from MoinMoin import config, wikiutil
from MoinMoin.Page import Page

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
        
    def stats(self, request, formatter, hitsFrom):
        """ Return search statistics, formatted with formatter

        @param request: current request
        @param formatter: formatter to use
        @param hitsFrom: current position in the hits
        @rtype: unicode
        @return formatted statistics
        """
        _ = request.getText
        output = [
            formatter.paragraph(1),
            formatter.text(_("Hits %(hitsFrom)d to %(hitsTo)d "
                "from %(hits)d results out of about %(pages)d pages.") %
                   {'hits': len(self.hits), 'pages': self.pages,
                       'hitsFrom': hitsFrom + 1,
                       'hitsTo': hitsFrom + request.cfg.search_results_per_page}),
            formatter.text(u' (%s)' %
                formatter.text(_("%.2f seconds") % self.elapsed)),
            formatter.paragraph(0),
            ]
        return ''.join(output)

    def pageList(self, request, formatter, info=0, numbered=1,
            paging=True, hitsFrom=0):
        """ Format a list of found pages

        @param request: current request
        @param formatter: formatter to use
        @param info: show match info in title
        @param numbered: use numbered list for display
        @param paging: toggle paging
        @param hitsFrom: current position in the hits
        @rtype: unicode
        @return formatted page list
        """
        self._reset(request, formatter)
        f = formatter
        write = self.buffer.write
        if numbered:
            list = lambda on: f.number_list(on, start=hitsFrom+1)
        else:
            list = f.bullet_list

        # Add pages formatted as list
        if self.hits:
            write(list(1))
            
            # XXX: Do some xapian magic here
            if paging:
                hitsTo = hitsFrom + request.cfg.search_results_per_page
                displayHits = self.hits[hitsFrom:hitsTo]
            else:
                displayHits = self.hits

            for page in displayHits:
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
            if paging:
                write(self.formatPrevNextPageLinks(hitsFrom=hitsFrom,
                    hitsPerPage=request.cfg.search_results_per_page,
                    hitsNum=len(self.hits)))

        return self.getvalue()

    def pageListWithContext(self, request, formatter, info=1, context=180,
                            maxlines=1, paging=True, hitsFrom=0):
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
        @param paging: toggle paging
        @param hitsFrom: current position in the hits
        @rtype: unicode
        @return formatted page list with context
        """
        self._reset(request, formatter)
        f = formatter
        write = self.buffer.write
        
        # Add pages formatted as definition list
        if self.hits:
            write(f.definition_list(1))

            # XXX: Do some xapian magic here
            if paging:
                hitsTo = hitsFrom+request.cfg.search_results_per_page
                displayHits = self.hits[hitsFrom:hitsTo]
            else:
                displayHits = self.hits

            for page in displayHits:
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
                elif page.page_name.startswith('FS/'): # XXX FS hardcoded
                    fmt_context = ""
                    querydict = None
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
            if paging:
                write(self.formatPrevNextPageLinks(hitsFrom=hitsFrom,
                    hitsPerPage=request.cfg.search_results_per_page,
                    hitsNum=len(self.hits)))
        
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
            if matches[i].start >= start and \
                    isinstance(matches[i], TextMatch):
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

    def formatPrevNextPageLinks(self, hitsFrom, hitsPerPage, hitsNum):
        """ Format previous and next page links in page

        @param hitsFrom: current position in the hits
        @param hitsPerPage: number of hits per page
        @param hitsNum: number of hits
        @rtype: unicode
        @return: links to previous and next pages (if exist)
        """
        _ = self.request.getText
        f = self.formatter
        from_re = r'\&from=[\d]+'
        uri = re.sub(from_re, '', self.request.request_uri)
        from_uri = lambda n: '%s&from=%i' % (uri, n)
        l = []
        if hitsFrom > 0:                        # previous page available
            n = hitsFrom - hitsPerPage
            if n < 0: n = 0
            l.append(''.join([
                f.url(1, href=from_uri(n)),
                _('Previous Page'),
                f.url(0)
            ]))
        if hitsFrom + hitsPerPage < hitsNum:    # next page available
            n = hitsFrom + hitsPerPage
            if n >= hitsNum: n = hitsNum - 1
            l.append(''.join([
                f.url(1, href=from_uri(n)),
                _('Next Page'),
                f.url(0)
            ]))
        return f.text(' | ').join(l)

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


def getSearchResults(request, query, hits, start):
    result_hits = []
    for wikiname, page, attachment, match in hits:
        if wikiname in (request.cfg.interwikiname, 'Self'): # a local match
            if attachment:
                result_hits.append(FoundAttachment(page.page_name, attachment))
            else:
                result_hits.append(FoundPage(page.page_name, match))
        else:
            result_hits.append(FoundRemote(wikiname, page, attachment, match))
    elapsed = time.time() - start
    count = request.rootpage.getPageCount()
    return SearchResults(query, result_hits, count, elapsed)

