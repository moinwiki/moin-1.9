# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - search engine internals

    @copyright: 2005 MoinMoin:FlorianFesti,
                2005 MoinMoin:NirSoffer,
                2005 MoinMoin:AlexanderSchremmer,
                2006-2009 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
    @license: GNU GPL, see COPYING for details
"""

import sys, os, time, errno, codecs

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil, config, caching
from MoinMoin.Page import Page
from MoinMoin.util import lock, filesys
from MoinMoin.search.results import getSearchResults, Match, TextMatch, TitleMatch, getSearchResults

##############################################################################
# Search Engine Abstraction
##############################################################################


class PageQueue(object):
    """
    Represents a locked page queue on the disk
    """

    def __init__(self, request, xapian_dir, queuename, timeout=10.0):
        """
        @param request: request object
        @param xapian_dir: the xapian main directory
        @param queuename: name of the queue (used for caching key)
        @param timeout: lock acquire timeout
        """
        self.request = request
        self.xapian_dir = xapian_dir
        self.queuename = queuename
        self.timeout = timeout

    def get_cache(self, locking):
        return caching.CacheEntry(self.request, self.xapian_dir, self.queuename,
                                  scope='dir', use_pickle=True, do_locking=locking)

    def exists(self):
        """ Checks if the queue exists on the filesystem """
        cache = self.get_cache(locking=False)
        return cache.exists()

    def _queue(self, cache):
        try:
            queue = cache.content()
        except caching.CacheError:
            # likely nothing there yet
            queue = []
        return queue

    def pages(self):
        """ Return list of pages in the queue """
        cache = self.get_cache(locking=True)
        return self._queue(cache)

    def append(self, pagename):
        """ Append a page to queue

        @param pagename: string to save
        """
        cache = self.get_cache(locking=False) # we lock manually
        cache.lock('w', 60.0)
        try:
            queue = self._queue(cache)
            queue.append(pagename)
            cache.update(queue)
        finally:
            cache.unlock()

    def remove(self, pages):
        """ Remove pages from the queue

        When the queue is empty, the queue file is removed, so exists()
        can tell if there is something waiting in the queue.

        @param pages: list of pagenames to remove
        """
        cache = self.get_cache(locking=False) # we lock manually
        cache.lock('w', 60.0)
        try:
            queue = self._queue(cache)
            for page in pages:
                try:
                    queue.remove(page)
                except ValueError:
                    pass
            if queue:
                cache.update(queue)
            else:
                cache.remove()
            return True
        finally:
            cache.unlock()
        return False


class BaseIndex(object):
    """ Represents a search engine index """

    class LockedException(Exception):
        pass

    def __init__(self, request):
        """
        @param request: current request
        """
        self.request = request
        main_dir = self._main_dir()
        self.dir = os.path.join(main_dir, 'index')
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        self.sig_file = os.path.join(main_dir, 'complete')
        lock_dir = os.path.join(main_dir, 'index-lock')
        self.lock = lock.WriteLock(lock_dir, timeout=3600.0, readlocktimeout=60.0)
        #self.read_lock = lock.ReadLock(lock_dir, timeout=3600.0)
        self.update_queue = PageQueue(request, main_dir, 'update-queue')
        self.remove_queue = PageQueue(request, main_dir, 'remove-queue')

        # Disabled until we have a sane way to build the index with a
        # queue in small steps.
        ## if not self.exists():
        ##    self.indexPagesInNewThread(request)

    def _main_dir(self):
        raise NotImplemented('...')

    def exists(self):
        """ Check if index exists """
        return os.path.exists(self.sig_file)

    def mtime(self):
        """ Modification time of the index """
        return os.path.getmtime(self.dir)

    def touch(self):
        """ Touch the index """
        filesys.touch(self.dir)

    def _search(self, query):
        """ Actually perfom the search (read-lock acquired)

        @param query: the search query objects tree
        """
        raise NotImplemented('...')

    def search(self, query, **kw):
        """ Search for items in the index

        @param query: the search query objects to pass to the index
        """
        #if not self.read_lock.acquire(1.0):
        #    raise self.LockedException
        #try:
        hits = self._search(query, **kw)
        #finally:
        #    self.read_lock.release()
        return hits

    def update_page(self, pagename, now=1):
        """ Update a single page in the index

        @param pagename: the name of the page to update
        @keyword now: do all updates now (default: 1)
        """
        self.update_queue.append(pagename)
        if now:
            self._do_queued_updates_InNewThread()

    def remove_item(self, pagename, attachment=None, now=1):
        """ Removes a page and all its revisions or a single attachment

        @param pagename: name of the page to be removed
        @keyword attachment: optional, only remove this attachment of the page
        @keyword now: do all updates now (default: 1)
        """
        self.remove_queue.append('%s//%s' % (pagename, attachment or ''))
        if now:
            self._do_queued_updates_InNewThread()

    def indexPages(self, files=None, mode='update', pages=None):
        """ Index pages (and files, if given)

        Can be called only from a script. To index pages during a user
        request, use indexPagesInNewThread.

        @param files: iterator or list of files to index additionally
        @param mode: set the mode of indexing the pages, either 'update', 'add' or 'rebuild'
        @param pages: list of pages to index, if not given, all pages are indexed
        """
        if not self.lock.acquire(1.0):
            logging.warning("can't index: can't acquire lock")
            return
        try:
            self._unsign()
            start = time.time()
            request = self._indexingRequest(self.request)
            self._index_pages(request, files, mode, pages=pages)
            logging.info("indexing completed successfully in %0.2f seconds." %
                        (time.time() - start))
            self._sign()
        finally:
            self.lock.release()

    def indexPagesInNewThread(self, files=None, mode='update', pages=None):
        """ Index pages in a new thread

        Should be called from a user request. From a script, use indexPages.
        """
        # Prevent rebuilding the index just after it was finished
        if self.exists():
            return

        from threading import Thread
        indexThread = Thread(target=self._index_pages, args=(self.request, files, mode, pages))
        indexThread.setDaemon(True)

        # Join the index thread after current request finish, prevent
        # Apache CGI from killing the process.
        def joinDecorator(finish):
            def func():
                finish()
                indexThread.join()
            return func

        self.request.finish = joinDecorator(self.request.finish)
        indexThread.start()

    def _index_pages(self, request, files=None, mode='update', pages=None):
        """ Index all pages (and all given files)

        This should be called from indexPages or indexPagesInNewThread only!

        This may take some time, depending on the size of the wiki and speed
        of the machine.

        When called in a new thread, lock is acquired before the call,
        and this method must release it when it finishes or fails.

        @param request: current request
        @param files: iterator or list of files to index additionally
        @param mode: set the mode of indexing the pages, either 'update',
        'add' or 'rebuild'
        @param pages: list of pages to index, if not given, all pages are indexed

        """
        raise NotImplemented('...')

    def _remove_item(self, writer, page, attachment=None):
        """ Remove a page and all its revisions from the index or just
            an attachment of that page

        @param pagename: name of the page to remove
        @keyword attachment: optionally, just remove this attachment
        """
        raise NotImplemented('...')

    def _do_queued_updates_InNewThread(self):
        """ do queued index updates in a new thread

        Should be called from a user request. From a script, use indexPages.
        """
        if not self.lock.acquire(1.0):
            logging.warning("can't index: can't acquire lock")
            return
        try:
            def lockedDecorator(f):
                def func(*args, **kwargs):
                    try:
                        return f(*args, **kwargs)
                    finally:
                        self.lock.release()
                return func

            from threading import Thread
            indexThread = Thread(
                    target=lockedDecorator(self._do_queued_updates),
                    args=(self._indexingRequest(self.request), ))
            indexThread.setDaemon(True)

            # Join the index thread after current request finish, prevent
            # Apache CGI from killing the process.
            def joinDecorator(finish):
                def func():
                    finish()
                    indexThread.join()
                return func

            self.request.finish = joinDecorator(self.request.finish)
            indexThread.start()
        except:
            self.lock.release()
            raise

    def _do_queued_updates(self, request, amount=5):
        """ Perform updates in the queues (read-lock acquired)

        @param request: the current request
        @keyword amount: how many updates to perform at once (default: 5)
        """
        raise NotImplemented('...')

    def optimize(self):
        """ Optimize the index if possible """
        raise NotImplemented('...')

    def contentfilter(self, filename):
        """ Get a filter for content of filename and return unicode content.

        @param filename: name of the file
        """
        request = self.request
        mt = wikiutil.MimeType(filename=filename)
        for modulename in mt.module_name():
            try:
                execute = wikiutil.importPlugin(request.cfg, 'filter', modulename)
                break
            except wikiutil.PluginMissingError:
                pass
            else:
                logging.info("Cannot load filter for mimetype %s" % modulename)
        try:
            data = execute(self, filename)
            logging.debug("Filter %s returned %d characters for file %s" % (modulename, len(data), filename))
        except (OSError, IOError), err:
            data = ''
            logging.warning("Filter %s threw error '%s' for file %s" % (modulename, str(err), filename))
        return mt.mime_type(), data

    def _indexingRequest(self, request):
        """ Return a new request that can be used for index building.

        This request uses a security policy that lets the current user
        read any page. Without this policy some pages will not render,
        which will create broken pagelinks index.

        @param request: current request
        """
        import copy
        from MoinMoin.security import Permissions
        from MoinMoin.logfile import editlog

        class SecurityPolicy(Permissions):

            def read(self, *args, **kw):
                return True

        r = copy.copy(request)
        r.user.may = SecurityPolicy(r.user)
        r.editlog = editlog.EditLog(r)
        return r

    def _unsign(self):
        """ Remove sig file - assume write lock acquired """
        try:
            os.remove(self.sig_file)
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise

    def _sign(self):
        """ Add sig file - assume write lock acquired """
        f = file(self.sig_file, 'w')
        try:
            f.write('')
        finally:
            f.close()


##############################################################################
### Searching
##############################################################################


class BaseSearch(object):
    """ A search run """

    def __init__(self, request, query, sort='weight', mtime=None, historysearch=0):
        """
        @param request: current request
        @param query: search query objects tree
        @keyword sort: the sorting of the results (default: 'weight')
        @keyword mtime: only show items newer than this timestamp (default: None)
        @keyword historysearch: whether to show old revisions of a page (default: 0)
        """
        self.request = request
        self.query = query
        self.sort = sort
        self.mtime = mtime
        self.historysearch = historysearch
        self.filtered = False
        self.fs_rootpage = "FS" # XXX FS hardcoded

    def run(self):
        """ Perform search and return results object """

        start = time.time()
        hits, estimated_hits = self._search()

        # important - filter deleted pages or pages the user may not read!
        if not self.filtered:
            hits = self._filter(hits)
            logging.debug("after filtering: %d hits" % len(hits))

        return self._get_search_results(hits, start, estimated_hits)

    def _search(self):
        """
        Search pages.

        Return list of tuples (wikiname, page object, attachment,
        matches, revision) and estimated number of search results (If
        there is no estimate, None should be returned).

        The list may contain deleted pages or pages the user may not read.
        """
        raise NotImplementedError()

    def _filter(self, hits):
        """
        Filter out deleted or acl protected pages

        @param hits: list of hits
        """
        userMayRead = self.request.user.may.read
        fs_rootpage = self.fs_rootpage + "/"
        thiswiki = (self.request.cfg.interwikiname, 'Self')
        filtered = [(wikiname, page, attachment, match, rev)
                for wikiname, page, attachment, match, rev in hits
                    if (not wikiname in thiswiki or
                       page.exists() and userMayRead(page.page_name) or
                       page.page_name.startswith(fs_rootpage)) and
                       (not self.mtime or self.mtime <= page.mtime_usecs()/1000000)]
        return filtered

    def _get_search_results(self, hits, start, estimated_hits):
        return getSearchResults(self.request, self.query, hits, start, self.sort, estimated_hits)

    def _get_match(self, page=None, uid=None):
        """
        Get all matches

        @param page: the current page instance
        """
        if page:
            return self.query.search(page)

    def _getHits(self, pages):
        """ Get the hit tuples in pages through _get_match """
        logging.debug("_getHits searching in %d pages ..." % len(pages))
        hits = []
        revisionCache = {}
        fs_rootpage = self.fs_rootpage
        for hit in pages:

            uid = hit.get('uid')
            wikiname = hit['wikiname']
            pagename = hit['pagename']
            attachment = hit['attachment']
            revision = int(hit.get('revision', 0))

            logging.debug("_getHits processing %r %r %d %r" % (wikiname, pagename, revision, attachment))

            if wikiname in (self.request.cfg.interwikiname, 'Self'): # THIS wiki
                page = Page(self.request, pagename, rev=revision)

                if not self.historysearch and revision:
                    revlist = page.getRevList()
                    # revlist can be empty if page was nuked/renamed since it was included in xapian index
                    if not revlist or revlist[0] != revision:
                        # nothing there at all or not the current revision
                        logging.debug("no history search, skipping non-current revision...")
                        continue

                if attachment:
                    # revision currently is 0 ever
                    if pagename == fs_rootpage: # not really an attachment
                        page = Page(self.request, "%s/%s" % (fs_rootpage, attachment))
                        hits.append((wikiname, page, None, None, revision))
                    else:
                        matches = self._get_match(page=None, uid=uid)
                        hits.append((wikiname, page, attachment, matches, revision))
                else:
                    matches = self._get_match(page=page, uid=uid)
                    logging.debug("self._get_match %r" % matches)
                    if matches:
                        if not self.historysearch and pagename in revisionCache and revisionCache[pagename][0] < revision:
                            hits.remove(revisionCache[pagename][1])
                            del revisionCache[pagename]
                        hits.append((wikiname, page, attachment, matches, revision))
                        revisionCache[pagename] = (revision, hits[-1])

            else: # other wiki
                hits.append((wikiname, pagename, attachment, None, revision))
        logging.debug("_getHits returning %r." % hits)
        return hits


class MoinSearch(BaseSearch):

    def __init__(self, request, query, sort='weight', mtime=None, historysearch=0, pages=None):
        super(MoinSearch, self).__init__(request, query, sort, mtime, historysearch)

        self.pages = pages

    def _search(self):
        """
        Search pages using moin's built-in full text search

        The list may contain deleted pages or pages the user may not
        read.

        if self.pages is not None, searches in that pages.
        """
        self.request.clock.start('_moinSearch')

        # if self.pages is none, we make a full pagelist, but don't
        # search attachments (thus attachment name = '')
        pages = self.pages or [{'pagename': p, 'attachment': '', 'wikiname': 'Self', } for p in self._getPageList()]

        hits = self._getHits(pages)
        self.request.clock.stop('_moinSearch')

        return hits, None

    def _getPageList(self):
        """ Get list of pages to search in

        If the query has a page filter, use it to filter pages before
        searching. If not, get a unfiltered page list. The filtering
        will happen later on the hits, which is faster with current
        slow storage.
        """
        filter_ = self.query.pageFilter()
        if filter_:
            # There is no need to filter the results again.
            self.filtered = True
            return self.request.rootpage.getPageList(filter=filter_)
        else:
            return self.request.rootpage.getPageList(user='', exists=0)

