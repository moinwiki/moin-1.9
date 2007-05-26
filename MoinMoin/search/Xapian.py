# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - xapian search engine

    @copyright: 2006 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
    @license: GNU GPL, see COPYING for details.
"""
debug = True

import os, re

import xapian
from xapian import Query

from MoinMoin.support.xapwrap import document as xapdoc
from MoinMoin.support.xapwrap import index as xapidx
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil
from MoinMoin.search.builtin import BaseIndex

try:
    # PyStemmer, snowball python bindings from http://snowball.tartarus.org/
    from Stemmer import Stemmer
except ImportError:
    Stemmer = None


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
    wikiword_re = re.compile(WikiParser.word_rule, re.U)

    token_re = re.compile(
        r"(?P<company>\w+[&@]\w+)|" + # company names like AT&T and Excite@Home.
        r"(?P<email>\w+([.-]\w+)*@\w+([.-]\w+)*)|" +    # email addresses
        r"(?P<hostname>\w+(\.\w+)+)|" +                 # hostnames
        r"(?P<num>(\w+[-/.,])*\w*\d\w*([-/.,]\w+)*)|" + # version numbers
        r"(?P<acronym>(\w\.)+)|" +          # acronyms: U.S.A., I.B.M., etc.
        r"(?P<word>\w+)",                   # words (including WikiWords)
        re.U)

    dot_re = re.compile(r"[-_/,.]")
    mail_re = re.compile(r"[-_/,.]|(@)")

    # XXX limit stuff above to xapdoc.MAX_KEY_LEN
    # WORD_RE = re.compile('\\w{1,%i}' % MAX_KEY_LEN, re.U)

    def __init__(self, request=None, language=None):
        """
        @param request: current request
        @param language: if given, the language in which to stem words
        """
        if request and request.cfg.xapian_stemming and language:
            self.stemmer = Stemmer(language)
        else:
            self.stemmer = None

    def raw_tokenize(self, value):
        """ Yield a stream of lower cased raw and stemmed words from a string.

        @param value: string to split, must be an unicode object or a list of
                      unicode objects
        """
        def enc(uc):
            """ 'encode' unicode results into whatever xapian wants """
            lower = uc.lower()
            return lower

        if isinstance(value, list): # used for page links
            for v in value:
                yield (enc(v), 0)
        else:
            tokenstream = re.finditer(self.token_re, value)
            for m in tokenstream:
                if m.group("acronym"):
                    yield (enc(m.group("acronym").replace('.', '')),
                            m.start())
                elif m.group("company"):
                    yield (enc(m.group("company")), m.start())
                elif m.group("email"):
                    displ = 0
                    for word in self.mail_re.split(m.group("email")):
                        if word:
                            yield (enc(word), m.start() + displ)
                            displ += len(word) + 1
                elif m.group("hostname"):
                    displ = 0
                    for word in self.dot_re.split(m.group("hostname")):
                        yield (enc(word), m.start() + displ)
                        displ += len(word) + 1
                elif m.group("num"):
                    displ = 0
                    for word in self.dot_re.split(m.group("num")):
                        yield (enc(word), m.start() + displ)
                        displ += len(word) + 1
                elif m.group("word"):
                    word = m.group("word")
                    yield (enc(word), m.start())
                    # if it is a CamelCaseWord, we additionally yield Camel, Case and Word
                    if self.wikiword_re.match(word):
                        for sm in re.finditer(self.singleword_re, word):
                            yield (enc(sm.group()), m.start() + sm.start())

    def tokenize(self, value, flat_stemming=True):
        """ Yield a stream of lower cased raw and stemmed words from a string.

        @param value: string to split, must be an unicode object or a list of
                      unicode objects
        @keyword flat_stemming: whether to yield stemmed terms automatically
                                with the natural forms (True) or
                                yield both at once as a tuple (False)
        """
        for word, pos in self.raw_tokenize(value):
            if flat_stemming:
                yield (word, pos)
                if self.stemmer:
                    yield (self.stemmer.stemWord(word), pos)
            else:
                yield (word, self.stemmer.stemWord(word), pos)


#############################################################################
### Indexing
#############################################################################

class Index(BaseIndex):
    """ A Xapian index """
    indexValueMap = {
        # mapping the value names we can easily fetch from the index to
        # integers required by xapian. 0 and 1 are reserved by xapwrap!
        'pagename': 2,
        'attachment': 3,
        'mtime': 4,
        'wikiname': 5,
        'revision': 6,
    }
    prefixMap = {
        # http://svn.xapian.org/*checkout*/trunk/xapian-applications/omega/docs/termprefixes.txt
        'author': 'A',
        'date': 'D',              # numeric format: YYYYMMDD or "latest" - e.g. D20050224 or Dlatest
                                  #G   newsGroup (or similar entity - e.g. a web forum name)
        'hostname': 'H',
        'keyword': 'K',
        'lang': 'L',              # ISO Language code
                                  #M   Month (numeric format: YYYYMM)
                                  #N   ISO couNtry code (or domaiN name)
                                  #P   Pathname
                                  #Q   uniQue id
        'raw': 'R',               # Raw (i.e. unstemmed) term
        'title': 'S',             # Subject (or title)
        'mimetype': 'T',
        'url': 'U',               # full URL of indexed document - if the resulting term would be > 240
                                  # characters, a hashing scheme is used to prevent overflowing
                                  # the Xapian term length limit (see omindex for how to do this).
                                  #W   "weak" (approximately 10 day intervals, taken as YYYYMMD from
                                  #  the D term, and changing the last digit to a '2' if it's a '3')
                                  #X   longer prefix for user-defined use
        'linkto': 'XLINKTO',      # this document links to that document
        'stem_lang': 'XSTEMLANG', # ISO Language code this document was stemmed in
        'category': 'XCAT',       # category this document belongs to
        'fulltitle': 'XFT',       # full title
        'domain': 'XDOMAIN',      # standard or underlay
        'revision': 'XREV',       # revision of page
                                  #Y   year (four digits)
    }

    def __init__(self, request):
        self._check_version()
        BaseIndex.__init__(self, request)

        # Check if we should and can stem words
        if request.cfg.xapian_stemming and not Stemmer:
            request.cfg.xapian_stemming = False

    def _check_version(self):
        """ Checks if the correct version of Xapian is installed """
        # every version greater than or equal to XAPIAN_MIN_VERSION is allowed
        XAPIAN_MIN_VERSION = (0, 9, 6)
        try:
           major, minor, revision = xapian.major_version(), xapian.minor_version(), xapian.revision()
        except AttributeError:
           major, minor, revision = xapian.xapian_major_version(), xapian.xapian_minor_version(), xapian.xapian_revision() # deprecated since xapian 0.9.6, removal in 1.1.0
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
        """ Perform the search using xapian (read-lock acquired)
        
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
                searcher = xapidx.ReadOnlyIndex(self.dir)
                searcher.configure(self.prefixMap, self.indexValueMap)
                timestamp = self.mtime()
                break

        kw = {}
        if sort == 'weight':
            # XXX: we need real weight here, like _moinSearch
            # (TradWeight in xapian)
            kw['sortByRelevence'] = True
            kw['sortKey'] = 'revision'
        if sort == 'page_name':
            kw['sortKey'] = 'pagename'

        hits = searcher.search(query, valuesWanted=['pagename',
            'attachment', 'mtime', 'wikiname', 'revision'], **kw)
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
            p = Page(request, name)
            if request.cfg.xapian_index_history:
                for rev in p.getRevList():
                    self._index_page(writer, Page(request, name, rev=rev), mode='update')
            else:
                self._index_page(writer, p, mode='update')
            self.update_queue.remove([name])

        # do page/attachment removals
        items = self.remove_queue.pages()[:amount]
        for item in items:
            _item = item.split('//')
            p = Page(request, _item[0])
            self._remove_item(writer, p, _item[1])
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
            wikiname = request.cfg.interwikiname or 'Self'
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
                    if debug: request.log("uid %r: mtime %r > docmtime %r == updated %r" % (uid, mtime, docmtime, updated))
                else:
                    uid = None
                    updated = True
            elif mode == 'add':
                updated = True
            if debug: request.log("%s %r" % (filename, updated))
            if updated:
                xitemid = xapdoc.Keyword('itemid', itemid)
                mimetype, file_content = self.contentfilter(filename)
                xwname = xapdoc.SortKey('wikiname', request.cfg.interwikiname or "Self")
                xpname = xapdoc.SortKey('pagename', fs_rootpage)
                xattachment = xapdoc.SortKey('attachment', filename) # XXX we should treat files like real pages, not attachments
                xmtime = xapdoc.SortKey('mtime', mtime)
                xrev = xapdoc.SortKey('revision', '0')
                title = " ".join(os.path.join(fs_rootpage, filename).split("/"))
                xtitle = xapdoc.Keyword('title', title)
                xmimetype = xapdoc.TextField('mimetype', mimetype, True)
                xcontent = xapdoc.TextField('content', file_content)
                doc = xapdoc.Document(textFields=(xcontent, xmimetype, ),
                                      keywords=(xtitle, xitemid, ),
                                      sortFields=(xpname, xattachment,
                                          xmtime, xwname, xrev, ),
                                     )
                doc.analyzerFactory = getWikiAnalyzerFactory()
                if mode == 'update':
                    if debug: request.log("%s (replace %r)" % (filename, uid))
                    doc.uid = uid
                    id = writer.index(doc)
                elif mode == 'add':
                    if debug: request.log("%s (add)" % (filename,))
                    id = writer.index(doc)
        except (OSError, IOError):
            pass

    def _get_languages(self, page):
        """ Get language of a page and the language to stem it in

        @param page: the page instance
        """
        lang = None
        default_lang = page.request.cfg.language_default

        # if we should stem, we check if we have stemmer for the
        # language available
        if page.request.cfg.xapian_stemming:
            lang = page.pi['language']
            try:
                Stemmer(lang)
                # if there is no exception, lang is stemmable
                return (lang, lang)
            except KeyError:
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
            prev, next = next, re.search(r'----*\r?\n', body[pos:])

        if not prev or prev == 1:
            return []

        return [cat.lower()
                for cat in re.findall(r'Category([^\s]+)', body[pos:])]

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

    def _index_page(self, writer, page, mode='update'):
        """ Index a page - assumes that the write lock is acquired

        @arg writer: the index writer object
        @arg page: a page object
        @arg mode: 'add' = just add, no checks
                   'update' = check if already in index and update if needed (mtime)
        """
        request = page.request
        wikiname = request.cfg.interwikiname or "Self"
        pagename = page.page_name
        mtime = page.mtime_usecs()
        revision = str(page.get_real_rev())
        itemid = "%s:%s:%s" % (wikiname, pagename, revision)
        author = page.last_edit(request)['editor']
        # XXX: Hack until we get proper metadata
        language, stem_language = self._get_languages(page)
        categories = self._get_categories(page)
        domains = tuple(self._get_domains(page))
        updated = False

        if mode == 'update':
            # from #xapian: if you generate a special "unique id" term,
            # you can just call database.replace_document(uid_term, doc)
            # -> done in xapwrap.index.Index.index()
            query = xapidx.RawQuery(xapdoc.makePairForWrite('itemid', itemid))
            enq, mset, docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', 'wikiname', ])
            if docs:
                doc = docs[0] # there should be only one
                uid = doc['uid']
                docmtime = long(doc['values']['mtime'])
                updated = mtime > docmtime
                if debug: request.log("uid %r: mtime %r > docmtime %r == updated %r" % (uid, mtime, docmtime, updated))
            else:
                uid = None
                updated = True
        elif mode == 'add':
            updated = True
        if debug: request.log("%s %r" % (pagename, updated))
        if updated:
            xwname = xapdoc.SortKey('wikiname', wikiname)
            xpname = xapdoc.SortKey('pagename', pagename)
            xattachment = xapdoc.SortKey('attachment', '') # this is a real page, not an attachment
            xmtime = xapdoc.SortKey('mtime', str(mtime))
            xrev = xapdoc.SortKey('revision', revision)
            xtitle = xapdoc.TextField('title', pagename, True) # prefixed
            xkeywords = [xapdoc.Keyword('itemid', itemid),
                    xapdoc.Keyword('lang', language),
                    xapdoc.Keyword('stem_lang', stem_language),
                    xapdoc.Keyword('fulltitle', pagename),
                    xapdoc.Keyword('revision', revision),
                    xapdoc.Keyword('author', author),
                ]
            for pagelink in page.getPageLinks(request):
                xkeywords.append(xapdoc.Keyword('linkto', pagelink))
            for category in categories:
                xkeywords.append(xapdoc.Keyword('category', category))
            for domain in domains:
                xkeywords.append(xapdoc.Keyword('domain', domain))
            xcontent = xapdoc.TextField('content', page.get_raw_body())
            doc = xapdoc.Document(textFields=(xcontent, xtitle),
                                  keywords=xkeywords,
                                  sortFields=(xpname, xattachment,
                                      xmtime, xwname, xrev),
                                 )
            doc.analyzerFactory = getWikiAnalyzerFactory(request,
                    stem_language)

            if mode == 'update':
                if debug: request.log("%s (replace %r)" % (pagename, uid))
                doc.uid = uid
                id = writer.index(doc)
            elif mode == 'add':
                if debug: request.log("%s (add)" % (pagename,))
                id = writer.index(doc)

        from MoinMoin.action import AttachFile

        attachments = AttachFile._get_files(request, pagename)
        for att in attachments:
            filename = AttachFile.getFilename(request, pagename, att)
            att_itemid = "%s:%s//%s" % (wikiname, pagename, att)
            mtime = wikiutil.timestamp2version(os.path.getmtime(filename))
            if mode == 'update':
                query = xapidx.RawQuery(xapdoc.makePairForWrite('itemid', att_itemid))
                enq, mset, docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', ])
                if debug: request.log("##%r %r" % (filename, docs))
                if docs:
                    doc = docs[0] # there should be only one
                    uid = doc['uid']
                    docmtime = long(doc['values']['mtime'])
                    updated = mtime > docmtime
                    if debug: request.log("uid %r: mtime %r > docmtime %r == updated %r" % (uid, mtime, docmtime, updated))
                else:
                    uid = None
                    updated = True
            elif mode == 'add':
                updated = True
            if debug: request.log("%s %s %r" % (pagename, att, updated))
            if updated:
                xatt_itemid = xapdoc.Keyword('itemid', att_itemid)
                xpname = xapdoc.SortKey('pagename', pagename)
                xwname = xapdoc.SortKey('wikiname', request.cfg.interwikiname or "Self")
                xattachment = xapdoc.SortKey('attachment', att) # this is an attachment, store its filename
                xmtime = xapdoc.SortKey('mtime', mtime)
                xrev = xapdoc.SortKey('revision', '0')
                xtitle = xapdoc.Keyword('title', '%s/%s' % (pagename, att))
                xlanguage = xapdoc.Keyword('lang', language)
                xstem_language = xapdoc.Keyword('stem_lang', stem_language)
                mimetype, att_content = self.contentfilter(filename)
                xmimetype = xapdoc.Keyword('mimetype', mimetype)
                xcontent = xapdoc.TextField('content', att_content)
                xtitle_txt = xapdoc.TextField('title',
                        '%s/%s' % (pagename, att), True)
                xfulltitle = xapdoc.Keyword('fulltitle', pagename)
                xdomains = [xapdoc.Keyword('domain', domain)
                        for domain in domains]
                doc = xapdoc.Document(textFields=(xcontent, xtitle_txt),
                                      keywords=xdomains + [xatt_itemid,
                                          xtitle, xlanguage, xstem_language,
                                          xmimetype, xfulltitle, ],
                                      sortFields=(xpname, xattachment, xmtime,
                                          xwname, xrev, ),
                                     )
                doc.analyzerFactory = getWikiAnalyzerFactory(request,
                        stem_language)
                if mode == 'update':
                    if debug: request.log("%s (replace %r)" % (pagename, uid))
                    doc.uid = uid
                    id = writer.index(doc)
                elif mode == 'add':
                    if debug: request.log("%s (add)" % (pagename,))
                    id = writer.index(doc)
        #writer.flush()

    def _remove_item(self, writer, page, attachment=None):
        request = page.request
        wikiname = request.cfg.interwikiname or 'Self'
        pagename = page.page_name

        if not attachment:
            # Remove all revisions and attachments from the index
            query = xapidx.RawQuery(xapidx.makePairForWrite(
                self.prefixMap['fulltitle'], pagename))
            enq, mset, docs = writer.search(query, valuesWanted=['pagename',
                'attachment', ])
            for doc in docs:
                writer.delete_document(doc['uid'])
                request.log('%s removed from xapian index' %
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
                request.log('attachment %s from %s removed from index' %
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
            writer = xapidx.Index(self.dir, True)
            writer.configure(self.prefixMap, self.indexValueMap)
            pages = request.rootpage.getPageList(user='', exists=1)
            request.log("indexing all (%d) pages..." % len(pages))
            for pagename in pages:
                p = Page(request, pagename)
                if request.cfg.xapian_index_history:
                    for rev in p.getRevList():
                        self._index_page(writer,
                                Page(request, pagename, rev=rev),
                                mode)
                else:
                    self._index_page(writer, p, mode)
            if files:
                request.log("indexing all files...")
                for fname in files:
                    fname = fname.strip()
                    self._index_file(request, writer, fname, mode)
            writer.close()
        finally:
            writer.__del__()

