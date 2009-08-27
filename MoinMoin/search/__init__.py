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
from MoinMoin.search.builtin import MoinSearch


def searchPages(request, query, sort='weight', mtime=None, historysearch=None, **kw):
    """
    Search the text of all pages for query.

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

    return _get_searcher(request, query, sort, mtime, historysearch, **kw).run()


def _get_searcher(request, query, sort='weight', mtime=None, historysearch=None, **kw):
    """
    Return a searcher object according to the configuration.
    """
    query = _parse_query(query, **kw)
    searcher = None

    if request.cfg.xapian_search:
        try:
            from MoinMoin.search.Xapian.search import XapianSearch, IndexDoesNotExistError
            searcher = XapianSearch(request, query, sort, mtime=mtime, historysearch=historysearch)
        except ImportError, error:
            logging.warning("%s. Either disable Xapian completetly in your wikiconfig or upgrade your Xapian installation" % str(error))
        except IndexDoesNotExistError:
            logging.warning("Xapian index does not exist. Please crate it. Slow moin search is used.")

    if searcher is None:
        searcher = MoinSearch(request, query, sort, mtime=mtime, historysearch=historysearch)

    return searcher

def _parse_query(query, **kw):
    if isinstance(query, str) or isinstance(query, unicode):
        query = QueryParser(**kw).parse_query(query)

    return query

