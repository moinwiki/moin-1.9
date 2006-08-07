# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - xapian indexing search engine

    @copyright: 2006 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
    @license: GNU GPL, see COPYING for details.
"""
debug = True

import sys, os, re, codecs, time, os
from pprint import pprint

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

class UnicodeQuery(xapian.Query):
    def __init__(self, *args, **kwargs):
        self.encoding = kwargs.get('encoding', config.charset)

        nargs = []
        for term in args:
            if isinstance(term, unicode):
                term = term.encode(self.encoding)
            elif isinstance(term, list) or isinstance(term, tuple):
                term = [t.encode(self.encoding) for t in term]
            nargs.append(term)

        xapian.Query.__init__(self, *nargs, **kwargs)


##############################################################################
### Tokenizer
##############################################################################

def getWikiAnalyzerFactory(request=None, language='en'):
    return (lambda: WikiAnalyzer(request, language))

class WikiAnalyzer:
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
        if request and request.cfg.xapian_stemming and language:
            self.stemmer = Stemmer(language)
        else:
            self.stemmer = None

    def raw_tokenize(self, value):
        def enc(uc):
            """ 'encode' unicode results into whatever xapian / xapwrap wants """
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
        """Yield a stream of lower cased raw and stemmed (optional) words from a string.
           value must be an UNICODE object or a list of unicode objects
        """
        for word, pos in self.raw_tokenize(value):
            if flat_stemming:
                # XXX: should we really use a prefix for that?
                # Index.prefixMap['raw'] + i
                yield (word, pos)
                if self.stemmer:
                    yield (self.stemmer.stemWord(word), pos)
            else:
                yield (word, self.stemmer.stemWord(word), pos)


#############################################################################
### Indexing
#############################################################################

class Index(BaseIndex):
    indexValueMap = {
        # mapping the value names we can easily fetch from the index to
        # integers required by xapian. 0 and 1 are reserved by xapwrap!
        'pagename': 2,
        'attachment': 3,
        'mtime': 4,
        'wikiname': 5,
    }
    prefixMap = {
        # http://svn.xapian.org/*checkout*/trunk/xapian-applications/omega/docs/termprefixes.txt
        'author': 'A',
        'date':   'D', # numeric format: YYYYMMDD or "latest" - e.g. D20050224 or Dlatest
                       #G   newsGroup (or similar entity - e.g. a web forum name)
        'hostname': 'H',
        'keyword': 'K',
        'lang': 'L',   # ISO Language code
                       #M   Month (numeric format: YYYYMM)
                       #N   ISO couNtry code (or domaiN name)
                       #P   Pathname
                       #Q   uniQue id
        'raw':  'R',   # Raw (i.e. unstemmed) term
        'title': 'S',  # Subject (or title)
        'mimetype': 'T',
        'url': 'U',    # full URL of indexed document - if the resulting term would be > 240
                       # characters, a hashing scheme is used to prevent overflowing
                       # the Xapian term length limit (see omindex for how to do this).
                       #W   "weak" (approximately 10 day intervals, taken as YYYYMMD from
                       #  the D term, and changing the last digit to a '2' if it's a '3')
                       #X   longer prefix for user-defined use
        'linkto': 'XLINKTO', # this document links to that document
        'stem_lang': 'XSTEMLANG', # ISO Language code this document was stemmed in
        'category': 'XCAT', # category this document belongs to
        'full_title': 'XFT', # full title (for regex)
                       #Y   year (four digits)
    }

    def __init__(self, request):
        BaseIndex.__init__(self, request)

        # Check if we should and can stem words
        if request.cfg.xapian_stemming and not Stemmer:
            request.cfg.xapian_stemming = False

    def _main_dir(self):
        if self.request.cfg.xapian_index_dir:
            return os.path.join(self.request.cfg.xapian_index_dir,
                    self.request.cfg.siteid)
        else:
            return os.path.join(self.request.cfg.cache_dir, 'xapian')

    def exists(self):
        """ Check if the Xapian index exists """
        return BaseIndex.exists(self) and os.listdir(self.dir)

    def _search(self, query):
        """ read lock must be acquired """
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
        
        hits = searcher.search(query, valuesWanted=['pagename', 'attachment', 'mtime', 'wikiname'])
        self.request.cfg.xapian_searchers.append((searcher, timestamp))
        return hits
    
    def _do_queued_updates(self, request, amount=5):
        """ Assumes that the write lock is acquired """
        self.touch()
        writer = xapidx.Index(self.dir, True)
        writer.configure(self.prefixMap, self.indexValueMap)
        pages = self.queue.pages()[:amount]
        for name in pages:
            p = Page(request, name)
            self._index_page(writer, p, mode='update')
            self.queue.remove([name])
        writer.close()

    def allterms(self):
        db = xapidx.ExceptionTranslater.openIndex(True, self.dir)
        i = db.allterms_begin()
        while i != db.allterms_end():
            yield i.get_term()
            i.next()

    def termpositions(self, uid, term):
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
                enq, docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', 'wikiname', ])
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
                title = " ".join(os.path.join(fs_rootpage, filename).split("/"))
                xtitle = xapdoc.Keyword('title', title)
                xmimetype = xapdoc.TextField('mimetype', mimetype, True)
                xcontent = xapdoc.TextField('content', file_content)
                doc = xapdoc.Document(textFields=(xcontent, xmimetype, ),
                                      keywords=(xtitle, xitemid, ),
                                      sortFields=(xpname, xattachment, xmtime, xwname, ),
                                     )
                doc.analyzerFactory = getWikiAnalyzerFactory()
                if mode == 'update':
                    if debug: request.log("%s (replace %r)" % (filename, uid))
                    doc.uid = uid
                    id = writer.index(doc)
                elif mode == 'add':
                    if debug: request.log("%s (add)" % (filename,))
                    id = writer.index(doc)
        except (OSError, IOError), err:
            pass

    def _get_languages(self, page):
        body = page.get_raw_body()
        default_lang = page.request.cfg.language_default

        lang = ''

        if page.request.cfg.xapian_stemming:
            for line in body.split('\n'):
                if line.startswith('#language'):
                    lang = line.split(' ')[1]
                    try:
                        Stemmer(lang)
                    except KeyError:
                        # lang is not stemmable
                        break
                    else:
                        # lang is stemmable
                        return (lang, lang)
                elif not line.startswith('#'):
                    break
        
        if not lang:
            # no lang found at all.. fallback to default language
            lang = default_lang

        # return actual lang and lang to stem in
        return (lang, default_lang)

    def _get_categories(self, page):
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
        itemid = "%s:%s" % (wikiname, pagename)
        # XXX: Hack until we get proper metadata
        language, stem_language = self._get_languages(page)
        categories = self._get_categories(page)
        updated = False

        if mode == 'update':
            # from #xapian: if you generate a special "unique id" term,
            # you can just call database.replace_document(uid_term, doc)
            # -> done in xapwrap.index.Index.index()
            query = xapidx.RawQuery(xapdoc.makePairForWrite('itemid', itemid))
            enq, docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', 'wikiname', ])
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
            xwname = xapdoc.SortKey('wikiname', request.cfg.interwikiname or "Self")
            xpname = xapdoc.SortKey('pagename', pagename)
            xattachment = xapdoc.SortKey('attachment', '') # this is a real page, not an attachment
            xmtime = xapdoc.SortKey('mtime', mtime)
            xtitle = xapdoc.TextField('title', pagename, True) # prefixed
            xkeywords = [xapdoc.Keyword('itemid', itemid),
                    xapdoc.Keyword('lang', language),
                    xapdoc.Keyword('stem_lang', stem_language),
                    xapdoc.Keyword('full_title', pagename.lower())]
            for pagelink in page.getPageLinks(request):
                xkeywords.append(xapdoc.Keyword('linkto', pagelink))
            for category in categories:
                xkeywords.append(xapdoc.Keyword('category', category))
            xcontent = xapdoc.TextField('content', page.get_raw_body())
            doc = xapdoc.Document(textFields=(xcontent, xtitle),
                                  keywords=xkeywords,
                                  sortFields=(xpname, xattachment, xmtime, xwname, ),
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
            att_itemid = "%s//%s" % (itemid, att)
            mtime = wikiutil.timestamp2version(os.path.getmtime(filename))
            if mode == 'update':
                query = xapidx.RawQuery(xapdoc.makePairForWrite('itemid', att_itemid))
                enq, docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', ])
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
                xattachment = xapdoc.SortKey('attachment', att) # this is an attachment, store its filename
                xmtime = xapdoc.SortKey('mtime', mtime)
                xtitle = xapdoc.Keyword('title', '%s/%s' % (pagename, att))
                xlanguage = xapdoc.Keyword('lang', language)
                xstem_language = xapdoc.Keyword('stem_lang', stem_language)
                mimetype, att_content = self.contentfilter(filename)
                xmimetype = xapdoc.TextField('mimetype', mimetype, True)
                xcontent = xapdoc.TextField('content', att_content)
                doc = xapdoc.Document(textFields=(xcontent, xmimetype, ),
                                      keywords=(xatt_itemid, xtitle, xlanguage, xstem_language, ),
                                      sortFields=(xpname, xattachment, xmtime, xwname, ),
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

    def _index_pages(self, request, files=None, mode='update'):
        """ Index all pages (and all given files)
        
        This should be called from indexPages or indexPagesInNewThread only!
        
        This may take some time, depending on the size of the wiki and speed
        of the machine.

        When called in a new thread, lock is acquired before the call,
        and this method must release it when it finishes or fails.
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
                self._index_page(writer, p, mode)
            if files:
                request.log("indexing all files...")
                for fname in files:
                    fname = fname.strip()
                    self._index_file(request, writer, fname, mode)
            writer.close()
        finally:
            writer.__del__()

def run_query(query, db):
    enquire = xapian.Enquire(db)
    parser = xapian.QueryParser()
    query = parser.parse_query(query, xapian.QueryParser.FLAG_WILDCARD)
    print query.get_description()
    enquire.set_query(query)
    return enquire.get_mset(0, 10)

def run(request):
    pass
    #print "Begin"
    #db = xapian.WritableDatabase(xapian.open('test.db',
    #                                         xapian.DB_CREATE_OR_OPEN))
    #
    # index_data(db) ???
    #del db
    #mset = run_query(sys.argv[1], db)
    #print mset.get_matches_estimated()
    #iterator = mset.begin()
    #while iterator != mset.end():
    #    print iterator.get_document().get_data()
    #    iterator.next()
    #for i in xrange(1,170):
    #    doc = db.get_document(i)
    #    print doc.get_data()

if __name__ == '__main__':
    run()


