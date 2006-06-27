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

import time, sys
from MoinMoin import wikiutil, config
from MoinMoin.Page import Page
from MoinMoin.search.results import FoundRemote, FoundPage, FoundAttachment, SearchResults

try:
    from MoinMoin.search import Xapian
except ImportError:
    pass


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
                        page = Page(self.request, "%s/%s" % (fs_rootpage, attachment))
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

