# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - xapian indexing search engine

    @copyright: 2006 MoinMoin:ThomasWaldmann,
                2006 MoinMoin:FranzPletz
    @license: GNU GPL, see COPYING for details.
"""
debug = True

import sys, os, re, codecs, errno, time
from pprint import pprint

import xapian
from xapian import Query
from MoinMoin.support.xapwrap import document as xapdoc
from MoinMoin.support.xapwrap import index as xapidx
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil
from MoinMoin.util import filesys, lock

try:
    # PyStemmer, snowball python bindings from http://snowball.tartarus.org/
    from Stemmer import Stemmer
    stemmer_available = True
except ImportError:
    stemmer_available = False

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
                yield enc(v)
        else:
            tokenstream = re.finditer(self.token_re, value)
            for m in tokenstream:
                if m.group("acronym"):
                    yield enc(m.group("acronym").replace('.', ''))
                elif m.group("company"):
                    yield enc(m.group("company"))
                elif m.group("email"):
                    for word in self.mail_re.split(m.group("email")):
                        if word:
                            yield enc(word)
                elif m.group("hostname"):
                    for word in self.dot_re.split(m.group("hostname")):
                        yield enc(word)
                elif m.group("num"):
                    for word in self.dot_re.split(m.group("num")):
                        yield enc(word)
                elif m.group("word"):
                    word = m.group("word")
                    yield enc(word)
                    # if it is a CamelCaseWord, we additionally yield Camel, Case and Word
                    if self.wikiword_re.match(word):
                        for sm in re.finditer(self.singleword_re, word):
                            yield enc(sm.group())

    def tokenize(self, value, flat_stemming=True):
        """Yield a stream of lower cased raw and stemmed (optional) words from a string.
           value must be an UNICODE object or a list of unicode objects
        """
        for i in self.raw_tokenize(value):
            if flat_stemming:
                yield i # XXX: should we really use a prefix for that? Index.prefixMap['raw'] + i
                if self.stemmer:
                    yield self.stemmer.stemWord(i)
            else:
                yield (i, self.stemmer.stemWord(i))


#############################################################################
### Indexing
#############################################################################

class UpdateQueue:
    def __init__(self, file, lock_dir):
        self.file = file
        self.writeLock = lock.WriteLock(lock_dir, timeout=10.0)
        self.readLock = lock.ReadLock(lock_dir, timeout=10.0)

    def exists(self):
        return os.path.exists(self.file)

    def append(self, pagename):
        """ Append a page to queue """
        if not self.writeLock.acquire(60.0):
            request.log("can't add %r to xapian update queue: can't lock queue" %
                        pagename)
            return
        try:
            f = codecs.open(self.file, 'a', config.charset)
            try:
                f.write(pagename + "\n")
            finally:
                f.close()
        finally:
            self.writeLock.release()

    def pages(self):
        """ Return list of pages in the queue """
        if self.readLock.acquire(1.0):
            try:
                return self._decode(self._read())
            finally:
                self.readLock.release()
        return []

    def remove(self, pages):
        """ Remove pages from the queue
        
        When the queue is empty, the queue file is removed, so exists()
        can tell if there is something waiting in the queue.
        """
        if self.writeLock.acquire(30.0):
            try:
                queue = self._decode(self._read())
                for page in pages:
                    try:
                        queue.remove(page)
                    except ValueError:
                        pass
                if queue:
                    self._write(queue)
                else:
                    self._removeFile()
                return True
            finally:
                self.writeLock.release()
        return False

    # Private -------------------------------------------------------

    def _decode(self, data):
        """ Decode queue data """
        pages = data.splitlines()
        return self._filterDuplicates(pages)

    def _filterDuplicates(self, pages):
        """ Filter duplicates in page list, keeping the order """
        unique = []
        seen = {}
        for name in pages:
            if not name in seen:
                unique.append(name)
                seen[name] = 1
        return unique

    def _read(self):
        """ Read and return queue data
        
        This does not do anything with the data so we can release the
        lock as soon as possible, enabling others to update the queue.
        """
        try:
            f = codecs.open(self.file, 'r', config.charset)
            try:
                return f.read()
            finally:
                f.close()
        except (OSError, IOError), err:
            if err.errno != errno.ENOENT:
                raise
            return ''

    def _write(self, pages):
        """ Write pages to queue file
        
        Requires queue write locking.
        """
        # XXX use tmpfile/move for atomic replace on real operating systems
        data = '\n'.join(pages) + '\n'
        f = codecs.open(self.file, 'w', config.charset)
        try:
            f.write(data)
        finally:
            f.close()

    def _removeFile(self):
        """ Remove queue file 
        
        Requires queue write locking.
        """
        try:
            os.remove(self.file)
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise


class Index:
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
                       #Y   year (four digits)
    }

    class LockedException(Exception):
        pass
    
    def __init__(self, request):
        self.request = request
        cache_dir = request.cfg.cache_dir
        main_dir = self._main_dir()
        self.dir = os.path.join(main_dir, 'index')
        filesys.makeDirs(self.dir)
        self.sig_file = os.path.join(main_dir, 'complete')
        lock_dir = os.path.join(main_dir, 'index-lock')
        self.lock = lock.WriteLock(lock_dir,
                                   timeout=3600.0, readlocktimeout=60.0)
        self.read_lock = lock.ReadLock(lock_dir, timeout=3600.0)
        self.queue = UpdateQueue(os.path.join(main_dir, 'update-queue'),
                                 os.path.join(main_dir, 'update-queue-lock'))

        # Disabled until we have a sane way to build the index with a
        # queue in small steps.
        ## if not self.exists():
        ##    self.indexPagesInNewThread(request)

        # Check if we should and can stem words
        if request.cfg.xapian_stemming and not stemmer_available:
            request.cfg.xapian_stemming = False

    def _main_dir(self):
        if self.request.cfg.xapian_index_dir:
            return os.path.join(self.request.cfg.xapian_index_dir,
                    self.request.cfg.siteid)
        else:
            return os.path.join(self.request.cfg.cache_dir, 'xapian')

    def exists(self):
        """ Check if index exists """        
        return os.path.exists(self.sig_file)
                
    def mtime(self):
        return os.path.getmtime(self.dir)

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
    
    def search(self, query):
        if not self.read_lock.acquire(1.0):
            raise self.LockedException
        try:
            hits = self._search(query)
        finally:
            self.read_lock.release()
        return hits

    def update_page(self, page):
        self.queue.append(page.page_name)
        self._do_queued_updates_InNewThread()

    def indexPages(self, files=None, mode='update'):
        """ Index all pages (and files, if given)
        
        Can be called only from a script. To index pages during a user
        request, use indexPagesInNewThread.
        @arg files: iterator or list of files to index additionally
        """
        if not self.lock.acquire(1.0):
            self.request.log("can't index: can't acquire lock")
            return
        try:
            request = self._indexingRequest(self.request)
            self._index_pages(request, None, files, mode)
        finally:
            self.lock.release()
    
    def indexPagesInNewThread(self, files=None, mode='update'):
        """ Index all pages in a new thread
        
        Should be called from a user request. From a script, use indexPages.
        """
        if not self.lock.acquire(1.0):
            self.request.log("can't index: can't acquire lock")
            return
        try:
            # Prevent rebuilding the index just after it was finished
            if self.exists():
                self.lock.release()
                return
            from threading import Thread
            indexThread = Thread(target=self._index_pages,
                args=(self._indexingRequest(self.request), self.lock, files, mode))
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

    def optimize(self):
        pass

    # Private ----------------------------------------------------------------

    def _do_queued_updates_InNewThread(self):
        """ do queued index updates in a new thread
        
        Should be called from a user request. From a script, use indexPages.
        """
        if not self.lock.acquire(1.0):
            self.request.log("can't index: can't acquire lock")
            return
        try:
            from threading import Thread
            indexThread = Thread(target=self._do_queued_updates,
                args=(self._indexingRequest(self.request), self.lock))
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

    def _do_queued_updates(self, request, lock=None, amount=5):
        """ Assumes that the write lock is acquired """
        try:
            writer = xapidx.Index(self.dir, True)
            writer.configure(self.prefixMap, self.indexValueMap)
            pages = self.queue.pages()[:amount]
            for name in pages:
                p = Page(request, name)
                self._index_page(writer, p, mode='update')
                self.queue.remove([name])
        finally:
            writer.close()
            if lock:
                lock.release()

    def contentfilter(self, filename):
        """ Get a filter for content of filename and return unicode content. """
        request = self.request
        mt = wikiutil.MimeType(filename=filename)
        for modulename in mt.module_name():
            try:
                execute = wikiutil.importPlugin(request.cfg, 'filter', modulename)
                break
            except wikiutil.PluginMissingError:
                pass
            else:
                request.log("Cannot load filter for mimetype." + modulename)
        try:
            data = execute(self, filename)
            if debug:
                request.log("Filter %s returned %d characters for file %s" % (modulename, len(data), filename))
        except (OSError, IOError), err:
            data = ''
            request.log("Filter %s threw error '%s' for file %s" % (modulename, str(err), filename))
        return mt.mime_type(), data
   
    def test(self, request):
        idx = xapidx.ReadOnlyIndex(self.dir)
        idx.configure(self.prefixMap, self.indexValueMap)
        print idx.search("is")
        #for d in docs:
        #    request.log("%r %r %r" % (d, d.get('attachment'), d.get('pagename')))

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
                docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', 'wikiname', ])
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
        updated = False

        if mode == 'update':
            # from #xapian: if you generate a special "unique id" term,
            # you can just call database.replace_document(uid_term, doc)
            # -> done in xapwrap.index.Index.index()
            query = xapidx.RawQuery(xapdoc.makePairForWrite('itemid', itemid))
            docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', 'wikiname', ])
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
                    xapdoc.Keyword('stem_lang', stem_language)]
            for pagelink in page.getPageLinks(request):
                xkeywords.append(xapdoc.Keyword('linkto', pagelink))
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
                docs = writer.search(query, valuesWanted=['pagename', 'attachment', 'mtime', ])
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
        

    def _index_pages(self, request, lock=None, files=None, mode='update'):
        """ Index all pages (and all given files)
        
        This should be called from indexPages or indexPagesInNewThread only!
        
        This may take some time, depending on the size of the wiki and speed
        of the machine.

        When called in a new thread, lock is acquired before the call,
        and this method must release it when it finishes or fails.
        """
        try:
            self._unsign()
            start = time.time()
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
            request.log("indexing completed successfully in %0.2f seconds." %
                        (time.time() - start))
            self._sign()
        finally:
            writer.__del__()
            if lock:
                lock.release()

    def _optimize(self, request):
        """ Optimize the index """
        pass

    def _indexingRequest(self, request):
        """ Return a new request that can be used for index building.
        
        This request uses a security policy that lets the current user
        read any page. Without this policy some pages will not render,
        which will create broken pagelinks index.        
        """
        from MoinMoin.request.CLI import Request
        from MoinMoin.security import Permissions
        request = Request(request.url)
        class SecurityPolicy(Permissions):
            def read(*args, **kw):
                return True        
        request.user.may = SecurityPolicy(request.user)
        return request

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


