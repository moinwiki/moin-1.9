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

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.search.queryparser import QueryParser, QueryError
from MoinMoin.search.builtin import Search

def searchPages(request, query, sort='weight', mtime=None, historysearch=None, **kw):
    """ Search the text of all pages for query.

    @param request: current request
    @param query: the expression (string or query objects) we want to search for
    @keyword sort: sorting of the search results, either 'weight' or 'page_name'
    @keyword mtime: only items modified since mtime
    @keyword historysearch: include older revisions of items in search
    @keyword titlesearch: treat all terms as title searches (passed to qp)
    @keyword case: do case sensitive search (passed to qp)
    @keyword regex: treat all terms as regular expression (passed to qp)
    @rtype: SearchResults instance
    @return: search results
    """
    if isinstance(query, str) or isinstance(query, unicode):
        query = QueryParser(**kw).parse_query(query)
    return Search(request, query, sort, mtime=mtime,
            historysearch=historysearch).run()

