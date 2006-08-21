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

from MoinMoin.search.queryparser import QueryParser
from MoinMoin.search.builtin import Search

def searchPages(request, query, sort='weight', mtime=None, **kw):
    """ Search the text of all pages for query.
    
    @param request: current request
    @param query: the expression (string or query objects) we want to search for
    @rtype: SearchResults instance
    @return: search results
    """
    if isinstance(query, str) or isinstance(query, unicode):
        query = QueryParser(**kw).parse_query(query)
    return Search(request, query, sort, mtime=mtime).run()

