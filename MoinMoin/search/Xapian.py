# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - xapian search engine

    @copyright: 2006-2008 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
    @license: GNU GPL, see COPYING for details.
"""

import os, re

import xapian
from xapian import Query

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.support import xappy
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil
from MoinMoin.search.builtin import BaseIndex


class UnicodeQuery(Query):
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
        self.add_field_action('attachment', INDEX_EXACT)
        self.add_field_action('attachment', STORE_CONTENT)
        self.add_field_action('mtime', INDEX_EXACT)
        self.add_field_action('revision', STORE_CONTENT)
        self.add_field_action('revision',  INDEX_EXACT)
        self.add_field_action('mimetype ', INDEX_EXACT)
        self.add_field_action('title', INDEX_FREETEXT, weight=5)
        self.add_field_action('content', INDEX_FREETEXT, spell=True)
        self.add_field_action('fulltittle',  INDEX_EXACT)
        self.add_field_action('domain',  INDEX_EXACT)
        self.add_field_action('lang ',  INDEX_EXACT)
        self.add_field_action('stem_lang ',  INDEX_EXACT)
        self.add_field_action('author',  INDEX_EXACT)
        self.add_field_action('linkto',  INDEX_EXACT)
        self.add_field_action('category',  INDEX_EXACT)


##############################################################################
### Tokenizer
##############################################################################

def getWikiAnalyzerFactory(request=None, language='en'):
    """ Returns a WikiAnalyzer instance

    @keyword request: current request object
    @keyword language: stemming language iso code, defaults to 'en'
    """
    return (lambda: WikiAnalyzer(request, language))

class WikiAnalyzer:
    """ A text analyzer for wiki syntax

    The purpose of this class is to anaylze texts/pages in wiki syntax
    and yield yielding single terms for xapwrap to feed into the xapian
    database.
    """

    singleword = r"[%(u)s][%(l)s]+" % {
                     'u': config.chars_upper,
                     'l': config.chars_lower,
                 }

    singleword_re = re.compile(singleword, re.U)
    wikiword_re = re.compile(WikiParser.word_rule, re.UNICODE|re.VERBOSE)

    token_re = re.compile(
        r"(?P<company>\w+[&@]\w+)|" + # company names like AT&T and Excite@Home.
        r"(?P<email>\w+([.-]\w+)*@\w+([.-]\w+)*)|" +    # email addresses
        r"(?P<acronym>(\w\.)+)|" +          # acronyms: U.S.A., I.B.M., etc.
        r"(?P<word>\w+)",                   # words (including WikiWords)
        re.U)

    dot_re = re.compile(r"[-_/,.]")
    mail_re = re.compile(r"[-_/,.]|(@)")
    alpha_num_re = re.compile(r"\d+|\D+")

    # XXX limit stuff above to xapdoc.MAX_KEY_LEN
    # WORD_RE = re.compile('\\w{1,%i}' % MAX_KEY_LEN, re.U)

    def __init__(self, request=None, language=None):
        """
        @param request: current request
        @param language: if given, the language in which to stem words
        """
        self.stemmer = None
        if request and request.cfg.xapian_stemming and language:
            try:
                stemmer = xapian.Stem(language)
                # we need this wrapper because the stemmer returns a utf-8
                # encoded string even when it gets fed with unicode objects:
                self.stemmer = lambda word: stemmer(word).decode('utf-8')
            except xapian.InvalidArgumentError:
                # lang is not stemmable or not available
                pass

    def raw_tokenize_word(self, word, pos):
        """ try to further tokenize some word starting at pos """
        yield (word, pos)
        if self.wikiword_re.match(word):
            # if it is a CamelCaseWord, we additionally try to tokenize Camel, Case and Word
            for m in re.finditer(self.singleword_re, word):
                mw, mp = m.group(), pos + m.start()
                for w, p in self.raw_tokenize_word(mw, mp):
                    yield (w, p)
        else:
            # if we have Foo42, yield Foo and 42
            for m in re.finditer(self.alpha_num_re, word):
                mw, mp = m.group(), pos + m.start()
                if mw != word:
                    for w, p in self.raw_tokenize_word(mw, mp):
                        yield (w, p)


    def raw_tokenize(self, value):
        """ Yield a stream of words from a string.

        @param value: string to split, must be an unicode object or a list of
                      unicode objects
        """
        if isinstance(value, list): # used for page links
            for v in value:
                yield (v, 0)
        else:
            tokenstream = re.finditer(self.token_re, value)
            for m in tokenstream:
                if m.group("acronym"):
                    yield (m.group("acronym").replace('.', ''), m.start())
                elif m.group("company"):
                    yield (m.group("company"), m.start())
                elif m.group("email"):
                    displ = 0
                    for word in self.mail_re.split(m.group("email")):
                        if word:
                            yield (word, m.start() + displ)
                            displ += len(word) + 1
                elif m.group("word"):
                    for word, pos in self.raw_tokenize_word(m.group("word"), m.start()):
                        yield word, pos

    def tokenize(self, value, flat_stemming=True):
        """ Yield a stream of lower cased raw and stemmed words from a string.

        @param value: string to split, must be an unicode object or a list of
                      unicode objects
        @keyword flat_stemming: whether to yield stemmed terms automatically
                                with the natural forms (True) or
                                yield both at once as a tuple (False)
        """
        for word, pos in self.raw_tokenize(value):
            word = word.lower() # transform it into what xapian wants
            if flat_stemming:
                yield (word, pos)
                if self.stemmer:
                    yield (self.stemmer(word), pos)
            else:
                yield (word, self.stemmer(word), pos)


#############################################################################
### Indexing
#############################################################################

class Index(BaseIndex):

    # XXX This is needed for a query parser. Since xappy uses
    # different terms, it is better to use xappy's query parser.
    prefixMap = {'title': 'S'}

    def __init__(self, request):
        self._check_version()
        BaseIndex.__init__(self, request)

    def _check_version(self):
        """ Checks if the correct version of Xapian is installed """
        # XXX xappy checks version on import! 
        # every version greater than or equal to XAPIAN_MIN_VERSION is allowed
        XAPIAN_MIN_VERSION = (1, 0, 0)
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
                searcher = xappy.SearchConnection(self.dir)
                timestamp = self.mtime()
                break

        kw = {}
        if sort == 'page_name':
            kw['sortby'] = 'pagename'

        # Try to get first 1000 hits.
        hits = searcher.search(query, 0, 1000, **kw)
        # If there are more hits, get them all
        if hits.more_matches:
            hits = searcher.search(query, 0, hits.matches_upper_bound, **kw)

        self.request.cfg.xapian_searchers.append((searcher, timestamp))
        return hits

    def _do_queued_updates(self, request, amount=5):
        """ Assumes that the write lock is acquired """
        self.touch()
        writer = xapidx.Index(self.dir, True)
        writer.configure(self.prefixMap, self.indexValueMap)

        # do all page updates
        pages = self.update_queue.pages()[:amount]
        for name in pages:
            self._index_page(request, writer, name, mode='update')
            self.update_queue.remove([name])

        # do page/attachment removals
        items = self.remove_queue.pages()[:amount]
        for item in items:
            _item = item.split('//')
            p = Page(request, _item[0])
            self._remove_item(request, writer, p, _item[1])
            self.remove_queue.remove([item])

        writer.close()

    def allterms(self):
        """ Fetches all terms in the Xapian index """
        db = xapidx.ExceptionTranslater.openIndex(True, self.dir)
        i = db.allterms_begin()
        while i != db.allterms_end():
            yield i.get_term()
            i.next()

    def termpositions(self, uid, term):
        """ Fetches all positions of a term in a document

        @param uid: document id of the item in the xapian index
        @param term: the term as a string
        """
        db = xapidx.ExceptionTranslater.openIndex(True, self.dir)
        pos = db.positionlist_begin(uid, term)
        while pos != db.positionlist_end(uid, term):
            yield pos.get_termpos()
            pos.next()

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
                query = xapidx.RawQuery(xapdoc.makePairForWrite('itemid', itemid))
                enq, mset, docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', 'wikiname', ])
                if docs:
                    doc = docs[0] # there should be only one
                    uid = doc['uid']
                    docmtime = long(doc['values']['mtime'])
                    updated = mtime > docmtime
                    logging.debug("uid %r: mtime %r > docmtime %r == updated %r" % (uid, mtime, docmtime, updated))
                else:
                    uid = None
                    updated = True
            elif mode == 'add':
                updated = True
            logging.debug("%s %r" % (filename, updated))
            if updated:
                xitemid = xapdoc.Keyword('itemid', itemid)
                mimetype, file_content = self.contentfilter(filename)
                xwname = xapdoc.SortKey('wikiname', request.cfg.interwikiname or u"Self")
                xpname = xapdoc.SortKey('pagename', fs_rootpage)
                xattachment = xapdoc.SortKey('attachment', filename) # XXX we should treat files like real pages, not attachments
                xmtime = xapdoc.SortKey('mtime', str(mtime))
                xrev = xapdoc.SortKey('revision', '0')
                title = " ".join(os.path.join(fs_rootpage, filename).split("/"))
                xtitle = xapdoc.Keyword('title', title)
                xmimetypes = [xapdoc.Keyword('mimetype', mt) for mt in [mimetype, ] + mimetype.split('/')]
                xcontent = xapdoc.TextField('content', file_content)
                doc = xapdoc.Document(textFields=(xcontent, ),
                                      keywords=xmimetypes + [xtitle, xitemid, ],
                                      sortFields=(xpname, xattachment,
                                          xmtime, xwname, xrev, ),
                                     )
                doc.analyzerFactory = getWikiAnalyzerFactory()
                if mode == 'update':
                    logging.debug("%s (replace %r)" % (filename, uid))
                    doc.uid = uid
                    id = writer.index(doc)
                elif mode == 'add':
                    logging.debug("%s (add)" % (filename, ))
                    id = writer.index(doc)
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
        return [m.group('all').lower() for m in self.request.cfg.cache.page_category_regex.finditer(body[pos:])]

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

    def _index_attachement(self):
        # XXX: refactor and call it from _index_page

        from MoinMoin.action import AttachFile
        wikiname = request.cfg.interwikiname or u"Self"
        # XXX: Hack until we get proper metadata
        language, stem_language = self._get_languages(p)
        domains = tuple(self._get_domains(p))
        updated = False

        attachments = AttachFile._get_files(request, pagename)
        for att in attachments:
            filename = AttachFile.getFilename(request, pagename, att)
            att_itemid = "%s:%s//%s" % (wikiname, pagename, att)
            mtime = wikiutil.timestamp2version(os.path.getmtime(filename))
            if mode == 'update':
                query = xapidx.RawQuery(xapdoc.makePairForWrite('itemid', att_itemid))
                enq, mset, docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', ])
                logging.debug("##%r %r" % (filename, docs))
                if docs:
                    doc = docs[0] # there should be only one
                    uid = doc['uid']
                    docmtime = long(doc['values']['mtime'])
                    updated = mtime > docmtime
                    logging.debug("uid %r: mtime %r > docmtime %r == updated %r" % (uid, mtime, docmtime, updated))
                else:
                    uid = None
                    updated = True
            elif mode == 'add':
                updated = True
            logging.debug("%s %s %r" % (pagename, att, updated))
            if updated:
                xatt_itemid = xapdoc.Keyword('itemid', att_itemid)
                xpname = xapdoc.SortKey('pagename', pagename)
                xwname = xapdoc.SortKey('wikiname', request.cfg.interwikiname or u"Self")
                xattachment = xapdoc.SortKey('attachment', att) # this is an attachment, store its filename
                xmtime = xapdoc.SortKey('mtime', str(mtime))
                xrev = xapdoc.SortKey('revision', '0')
                xtitle = xapdoc.Keyword('title', '%s/%s' % (pagename, att))
                xlanguage = xapdoc.Keyword('lang', language)
                xstem_language = xapdoc.Keyword('stem_lang', stem_language)
                mimetype, att_content = self.contentfilter(filename)
                xmimetypes = [xapdoc.Keyword('mimetype', mt) for mt in [mimetype, ] + mimetype.split('/')]
                xcontent = xapdoc.TextField('content', att_content)
                xtitle_txt = xapdoc.TextField('title', '%s/%s' % (pagename, att), True)
                xfulltitle = xapdoc.Keyword('fulltitle', pagename)
                xdomains = [xapdoc.Keyword('domain', domain) for domain in domains]
                doc = xapdoc.Document(textFields=(xcontent, xtitle_txt),
                                      keywords=xdomains + xmimetypes + [xatt_itemid,
                                          xtitle, xlanguage, xstem_language,
                                          xfulltitle, ],
                                      sortFields=(xpname, xattachment, xmtime,
                                          xwname, xrev, ),
                                     )
                doc.analyzerFactory = getWikiAnalyzerFactory(request, stem_language)
                if mode == 'update':
                    logging.debug("%s (replace %r)" % (pagename, uid))
                    doc.uid = uid
                    id = writer.index(doc)
                elif mode == 'add':
                    logging.debug("%s (add)" % (pagename, ))
                    id = writer.index(doc)
        #writer.flush()

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
            doc.fields.append(xappy.Field('revision', revision))
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

    def _remove_item(self, request, writer, page, attachment=None):
        wikiname = request.cfg.interwikiname or u'Self'
        pagename = page.page_name

        if not attachment:
            # Remove all revisions and attachments from the index
            query = xapidx.RawQuery(xapidx.makePairForWrite(
                self.prefixMap['fulltitle'], pagename))
            enq, mset, docs = writer.search(query, valuesWanted=['pagename',
                'attachment', ])
            for doc in docs:
                writer.delete_document(doc['uid'])
                logging.debug('%s removed from xapian index' %
                        doc['values']['pagename'])
        else:
            # Only remove a single attachment
            query = xapidx.RawQuery(xapidx.makePairForWrite('itemid',
                "%s:%s//%s" % (wikiname, pagename, attachment)))
            enq, mset, docs = writer.search(query, valuesWanted=['pagename',
                'attachment', ])
            if docs:
                doc = docs[0] # there should be only one
                writer.delete_document(doc['uid'])
                logging.debug('attachment %s from %s removed from index' %
                    (doc['values']['attachment'], doc['values']['pagename']))

    def _index_pages(self, request, files=None, mode='update'):
        """ Index all pages (and all given files)

        This should be called from indexPages or indexPagesInNewThread only!

        This may take some time, depending on the size of the wiki and speed
        of the machine.

        When called in a new thread, lock is acquired before the call,
        and this method must release it when it finishes or fails.

        @param request: the current request
        @keyword files: an optional list of files to index
        @keyword mode: how to index the files, either 'add', 'update' or
                       'rebuild'
        """

        # rebuilding the DB: delete it and add everything
        if mode == 'rebuild':
            for f in os.listdir(self.dir):
                os.unlink(os.path.join(self.dir, f))
            mode = 'add'

        try:
            self.touch()
            connection = MoinIndexerConnection(self.dir)
            # writer.configure(self.prefixMap, self.indexValueMap)
            pages = request.rootpage.getPageList(user='', exists=1)
            logging.debug("indexing all (%d) pages..." % len(pages))
            for pagename in pages:
                self._index_page(request, connection, pagename, mode=mode)
            if files:
                logging.debug("indexing all files...")
                for fname in files:
                    fname = fname.strip()
                    # XXX refactor _index_file
                    # self._index_file(request, connection, fname, mode)
            connection.flush()
            connection.close()
        finally:
            pass
            #connection.__del__()

