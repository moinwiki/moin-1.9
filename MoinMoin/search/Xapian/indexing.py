# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - xapian search engine indexing

    @copyright: 2006-2008 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
                2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""

import os, re
import xapian

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.support import xappy
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser
from MoinMoin.search.builtin import BaseIndex

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil


class Query(xapian.Query):
    pass


class UnicodeQuery(xapian.Query):
    """ Xapian query object which automatically encodes unicode strings """

    def __init__(self, *args, **kwargs):
        """
        @keyword encoding: specifiy the encoding manually (default: value of config.charset)
        """
        self.encoding = kwargs.get('encoding', config.charset)

        nargs = []
        for term in args:
            if isinstance(term, unicode):
                term = term.encode(self.encoding)
            elif isinstance(term, list) or isinstance(term, tuple):
                term = [t.encode(self.encoding) for t in term]
            nargs.append(term)

        Query.__init__(self, *nargs, **kwargs)


class MoinSearchConnection(xappy.SearchConnection):

    def get_all_documents(self):
        """
        Return all the documents in the xapian index.
        """
        document_count = self.get_doccount()
        query = self.query_all()
        hits = self.search(query, 0, document_count)
        return hits

    def get_all_documents_with_field(self, field, field_value):
        document_count = self.get_doccount()
        query = self.query_field(field, field_value)
        hits = self.search(query, 0, document_count)
        return hits


class MoinIndexerConnection(xappy.IndexerConnection):

    def __init__(self, *args, **kwargs):

        super(MoinIndexerConnection, self).__init__(*args, **kwargs)

        self._define_fields_actions()

    def _define_fields_actions(self):
        SORTABLE = xappy.FieldActions.SORTABLE
        INDEX_EXACT = xappy.FieldActions.INDEX_EXACT
        INDEX_FREETEXT = xappy.FieldActions.INDEX_FREETEXT
        STORE_CONTENT = xappy.FieldActions.STORE_CONTENT

        self.add_field_action('wikiname', INDEX_EXACT)
        self.add_field_action('wikiname', STORE_CONTENT)
        self.add_field_action('pagename', INDEX_EXACT)
        self.add_field_action('pagename', STORE_CONTENT)
        self.add_field_action('pagename', SORTABLE)
        self.add_field_action('attachment', INDEX_EXACT)
        self.add_field_action('attachment', STORE_CONTENT)
        self.add_field_action('mtime', INDEX_EXACT)
        self.add_field_action('mtime', STORE_CONTENT)
        self.add_field_action('revision', STORE_CONTENT)
        self.add_field_action('revision', INDEX_EXACT)
        self.add_field_action('mimetype', INDEX_EXACT)
        self.add_field_action('mimetype', STORE_CONTENT)
        self.add_field_action('title', INDEX_FREETEXT, weight=5)
        self.add_field_action('content', INDEX_FREETEXT, spell=True)
        self.add_field_action('fulltitle', INDEX_EXACT)
        self.add_field_action('fulltitle', STORE_CONTENT)
        self.add_field_action('domain', INDEX_EXACT)
        self.add_field_action('domain', STORE_CONTENT)
        self.add_field_action('lang', INDEX_EXACT)
        self.add_field_action('lang', STORE_CONTENT)
        self.add_field_action('stem_lang', INDEX_EXACT)
        self.add_field_action('author', INDEX_EXACT)
        self.add_field_action('linkto', INDEX_EXACT)
        self.add_field_action('linkto', STORE_CONTENT)
        self.add_field_action('category', INDEX_EXACT)
        self.add_field_action('category', STORE_CONTENT)


class Index(BaseIndex):

    def __init__(self, request):
        self._check_version()
        BaseIndex.__init__(self, request)

    def _check_version(self):
        """ Checks if the correct version of Xapian is installed """
        # every version greater than or equal to XAPIAN_MIN_VERSION is allowed
        XAPIAN_MIN_VERSION = (1, 0, 6)
        major, minor, revision = xapian.major_version(), xapian.minor_version(), xapian.revision()
        if (major, minor, revision) >= XAPIAN_MIN_VERSION:
            return

        from MoinMoin.error import ConfigurationError
        raise ConfigurationError(('MoinMoin needs at least Xapian version '
                '%d.%d.%d to work correctly. Either disable Xapian '
                'completetly in your wikiconfig or upgrade your Xapian %d.%d.%d '
                'installation!') % (XAPIAN_MIN_VERSION + (major, minor, revision)))

    def _main_dir(self):
        """ Get the directory of the xapian index """
        if self.request.cfg.xapian_index_dir:
            return os.path.join(self.request.cfg.xapian_index_dir,
                    self.request.cfg.siteid)
        else:
            return os.path.join(self.request.cfg.cache_dir, 'xapian')

    def exists(self):
        """ Check if the Xapian index exists """
        return BaseIndex.exists(self) and os.listdir(self.dir)

    def _search(self, query, sort='weight', historysearch=0):
        """
        Perform the search using xapian (read-lock acquired)

        @param query: the search query objects
        @keyword sort: the sorting of the results (default: 'weight')
        @keyword historysearch: whether to search in all page revisions (default: 0) TODO: use/implement this
        """
        while True:
            try:
                searcher, timestamp = self.request.cfg.xapian_searchers.pop()
                if timestamp != self.mtime():
                    searcher.close()
                else:
                    break
            except IndexError:
                searcher = MoinSearchConnection(self.dir)
                timestamp = self.mtime()
                break

        kw = {}
        if sort == 'page_name':
            kw['sortby'] = 'pagename'

        # Refresh connection, since it may be outdated.
        searcher.reopen()
        query = query.xapian_term(self.request, searcher)

        # Get maximum possible amount of hits from xappy, which is number of documents in the index.
        document_count = searcher.get_doccount()
        hits = searcher.search(query, 0, document_count, **kw)

        self.request.cfg.xapian_searchers.append((searcher, timestamp))
        return hits

    def _do_queued_updates(self, request, amount=5):
        """ Assumes that the write lock is acquired """
        self.touch()
        connection = MoinIndexerConnection(self.dir)
        # do all page updates
        pages = self.update_queue.pages()[:amount]
        for name in pages:
            self._index_page(request, connection, name, mode='update')
            self.update_queue.remove([name])

        # do page/attachment removals
        items = self.remove_queue.pages()[:amount]
        for item in items:
            assert len(item.split('//')) == 2
            pagename,  attachment = item.split('//')
            page = Page(request, pagename)
            self._remove_item(request, connection, page, attachment)
            self.remove_queue.remove([item])

        connection.close()

    def termpositions(self, uid, term):
        """ Fetches all positions of a term in a document

        @param uid: document id of the item in the xapian index
        @param term: the term as a string
        """
        raise NotImplementedError, "XXX xappy doesn't require this"

    def _index_file(self, request, writer, filename, mode='update'):
        """ index a file as it were a page named pagename
            Assumes that the write lock is acquired
        """
        fs_rootpage = 'FS' # XXX FS hardcoded

        try:
            wikiname = request.cfg.interwikiname or u'Self'
            itemid = "%s:%s" % (wikiname, os.path.join(fs_rootpage, filename))
            mtime = os.path.getmtime(filename)
            mtime = wikiutil.timestamp2version(mtime)
            if mode == 'update':
                try:
                    doc = connection.get_document(itemid)
                    docmtime = long(doc.data['mtime'])
                    updated = mtime > docmtime
                    logging.debug("itemid %r: mtime %r > docmtime %r == updated %r" % (itemid, mtime, docmtime, updated))
                except KeyError:
                    updated = True
                    doc = xappy.UnprocessedDocument()
                    doc.id = itemid
                    updated = mtime > docmtime

            elif mode == 'add':
                updated = True
                doc = xappy.UnprocessedDocument()
                doc.id = itemid

            logging.debug("%s %r" % (filename, updated))

            if updated:
                doc.fields.append(xappy.Field('wikiname', wikiname))
                doc.fields.append(xappy.Field('pagename', fs_rootpage))
                doc.fields.append(xappy.Field('attachment', filename)) # XXX we should treat files like real pages, not attachments

                doc.fields.append(xappy.Field('mtime', str(mtime)))
                doc.fields.append(xappy.Field('revision', '0'))
                title = " ".join(os.path.join(fs_rootpage, filename).split("/"))
                doc.fields.append(xappy.Field('title', title))

                mimetype, file_content = self.contentfilter(filename)
                doc.fields.extend([xappy.Field('mimetype', mt) for mt in [mimetype, ] + mimetype.split('/')])
                doc.fields.append(xappy.Field('content', file_content))

                # Stemming
                # doc.analyzerFactory = getWikiAnalyzerFactory()

                connection.replace(doc)

        except (OSError, IOError):
            pass

    def _get_languages(self, page):
        """ Get language of a page and the language to stem it in

        @param page: the page instance
        """
        lang = None
        default_lang = page.request.cfg.language_default

        # if we should stem, we check if we have stemmer for the language available
        if page.request.cfg.xapian_stemming:
            lang = page.pi['language']
            try:
                xapian.Stem(lang)
                # if there is no exception, lang is stemmable
                return (lang, lang)
            except xapian.InvalidArgumentError:
                # lang is not stemmable
                pass

        if not lang:
            # no lang found at all.. fallback to default language
            lang = default_lang

        # return actual lang and lang to stem in
        return (lang, default_lang)

    def _get_categories(self, page):
        """ Get all categories the page belongs to through the old
            regular expression

        @param page: the page instance
        """
        body = page.get_raw_body()

        prev, next = (0, 1)
        pos = 0
        while next:
            if next != 1:
                pos += next.end()
            prev, next = next, re.search(r'-----*\s*\r?\n', body[pos:])

        if not prev or prev == 1:
            return []
        # for CategoryFoo, group 'all' matched CategoryFoo, group 'key' matched just Foo
        return [m.group('all') for m in self.request.cfg.cache.page_category_regex.finditer(body[pos:])]

    def _get_domains(self, page):
        """ Returns a generator with all the domains the page belongs to

        @param page: page
        """
        if page.isUnderlayPage():
            yield 'underlay'
        if page.isStandardPage():
            yield 'standard'
        if wikiutil.isSystemPage(self.request, page.page_name):
            yield 'system'

    def _index_page(self, request, connection, pagename, mode='update'):
        """ Index a page - assumes that the write lock is acquired

        @arg connection: the Indexer connection object
        @arg pagename: a page name
        @arg mode: 'add' = just add, no checks
                   'update' = check if already in index and update if needed (mtime)
        """
        p = Page(request, pagename)
        if request.cfg.xapian_index_history:
            for rev in p.getRevList():
                updated = self._index_page_rev(request, connection, Page(request, pagename, rev=rev), mode=mode)
                logging.debug("updated page %r rev %d (updated==%r)" % (pagename, rev, updated))
                if not updated:
                    # we reached the revisions that are already present in the index
                    break
        else:
            self._index_page_rev(request, connection, p, mode=mode)

        self._index_attachments(request, connection, pagename, mode)

    def _index_attachments(self, request, connection, pagename, mode='update'):
        from MoinMoin.action import AttachFile

        wikiname = request.cfg.interwikiname or u"Self"
        # XXX: Hack until we get proper metadata
        p = Page(request, pagename)
        language, stem_language = self._get_languages(p)
        domains = tuple(self._get_domains(p))
        updated = False

        attachments = AttachFile._get_files(request, pagename)
        for att in attachments:
            filename = AttachFile.getFilename(request, pagename, att)
            itemid = "%s:%s//%s" % (wikiname, pagename, att)
            mtime = wikiutil.timestamp2version(os.path.getmtime(filename))
            if mode == 'update':
                try:
                    doc = connection.get_document(itemid)
                    docmtime = long(doc.data['mtime'])
                    updated = mtime > docmtime
                except KeyError:
                    updated = True
                    doc = xappy.UnprocessedDocument()
                    doc.id = itemid
            elif mode == 'add':
                updated = True
                doc = xappy.UnprocessedDocument()
                doc.id = itemid

            logging.debug("%s %s %r" % (pagename, att, updated))

            if updated:
                doc.fields.append(xappy.Field('wikiname', wikiname))
                doc.fields.append(xappy.Field('pagename', pagename))
                doc.fields.append(xappy.Field('attachment', att))

                doc.fields.append(xappy.Field('mtime', str(mtime)))
                doc.fields.append(xappy.Field('revision', '0'))
                doc.fields.append(xappy.Field('title', '%s/%s' % (pagename, att)))

                doc.fields.append(xappy.Field('lang', language))
                doc.fields.append(xappy.Field('stem_lang', stem_language))
                doc.fields.append(xappy.Field('fulltitle', pagename))

                mimetype, att_content = self.contentfilter(filename)
                doc.fields.extend([xappy.Field('mimetype', mt) for mt in [mimetype, ] + mimetype.split('/')])
                doc.fields.append(xappy.Field('content', att_content))
                doc.fields.extend([xappy.Field('domain', domain) for domain in domains])

                # XXX Stemming
                # doc.analyzerFactory = getWikiAnalyzerFactory(request, stem_language)
                connection.replace(doc)

    def _index_page_rev(self, request, connection, page, mode='update'):
        """ Index a page revision - assumes that the write lock is acquired

        @arg connection: the Indexer connection object
        @arg page: a page object
        @arg mode: 'add' = just add, no checks
                   'update' = check if already in index and update if needed (mtime)
        """
        request.page = page
        wikiname = request.cfg.interwikiname or u"Self"
        pagename = page.page_name
        mtime = page.mtime_usecs()
        revision = str(page.get_real_rev())
        itemid = "%s:%s:%s" % (wikiname, pagename, revision)
        author = page.edit_info().get('editor', '?')
        # XXX: Hack until we get proper metadata
        language, stem_language = self._get_languages(page)
        categories = self._get_categories(page)
        domains = tuple(self._get_domains(page))
        updated = False

        if mode == 'update':
            try:
                doc = connection.get_document(itemid)
                docmtime = long(doc.data['mtime'])
                updated = mtime > docmtime
                logging.debug("itemid %r: mtime %r > docmtime %r == updated %r" % (itemid, mtime, docmtime, updated))
            except KeyError:
                updated = True
                doc = xappy.UnprocessedDocument()
                doc.id = itemid

        elif mode == 'add':
            updated = True
            doc = xappy.UnprocessedDocument()
            doc.id = itemid


        logging.debug("%s %r" % (pagename, updated))

        if updated:
            doc.fields.append(xappy.Field('wikiname', wikiname))
            doc.fields.append(xappy.Field('pagename', pagename))
            doc.fields.append(xappy.Field('attachment', '')) # this is a real page, not an attachment
            doc.fields.append(xappy.Field('mtime', str(mtime)))
            doc.fields.append(xappy.Field('revision', revision))
            doc.fields.append(xappy.Field('title', pagename))

            doc.fields.append(xappy.Field('lang', language))
            doc.fields.append(xappy.Field('stem_lang', stem_language))
            doc.fields.append(xappy.Field('fulltitle', pagename))
            doc.fields.append(xappy.Field('author', author))

            mimetype = 'text/%s' % page.pi['format']  # XXX improve this
            doc.fields.extend([xappy.Field('mimetype', mt) for mt in [mimetype, ] + mimetype.split('/')])

            doc.fields.extend([xappy.Field('linkto', pagelink) for pagelink in page.getPageLinks(request)])
            doc.fields.extend([xappy.Field('category', category) for category in categories])
            doc.fields.extend([xappy.Field('domain', domain) for domain in domains])

            doc.fields.append(xappy.Field('content', page.get_raw_body()))

            # XXX Stemming
            # doc.analyzerFactory = getWikiAnalyzerFactory(request, stem_language)

            logging.debug("%s (replace %r)" % (pagename, itemid))
            connection.replace(doc)

        return updated

    def _remove_item(self, request, connection, page, attachment=None):
        wikiname = request.cfg.interwikiname or u'Self'
        pagename = page.page_name

        if not attachment:

            search_connection = MoinSearchConnection(self.dir)
            docs_to_delete = search_connection.get_all_documents_with_field('fulltitle', pagename)
            ids_to_delete = [d.id for d in docs_to_delete]
            search_connection.close()

            for id in ids_to_delete:
                connection.delete(id)
                logging.debug('%s removed from xapian index' % pagename)
        else:
            # Only remove a single attachment
            id = "%s:%s//%s" % (wikiname, pagename, attachment)
            connection.delete(id)

            logging.debug('attachment %s from %s removed from index' % (attachment, pagename))

    def _index_pages(self, request, files=None, mode='update', pages=None):
        """ Index pages (and all given files)

        This should be called from indexPages or indexPagesInNewThread only!

        This may take some time, depending on the size of the wiki and speed
        of the machine.

        When called in a new thread, lock is acquired before the call,
        and this method must release it when it finishes or fails.

        @param request: the current request
        @param files: an optional list of files to index
        @param mode: how to index the files, either 'add', 'update' or 'rebuild'
        @param pages: list of pages to index, if not given, all pages are indexed

        """
        if pages is None:
            # Index all pages
            pages = request.rootpage.getPageList(user='', exists=1)

        # rebuilding the DB: delete it and add everything
        if mode == 'rebuild':
            for f in os.listdir(self.dir):
                os.unlink(os.path.join(self.dir, f))
            mode = 'add'

        connection = MoinIndexerConnection(self.dir)
        try:
            self.touch()
            logging.debug("indexing all (%d) pages..." % len(pages))
            for pagename in pages:
                self._index_page(request, connection, pagename, mode=mode)
            if files:
                logging.debug("indexing all files...")
                for fname in files:
                    fname = fname.strip()
                    self._index_file(request, connection, fname, mode)
            connection.flush()
        finally:
            connection.close()

