# Copyright (c) 2005 Divmod Inc. See LICENSE file for details.
"""
Xapwrap provides an improved interface to the Xapian text indexing
library (see http://www.xapian.org/ for more information on
Xapian). Xapwrap provides a layered approach offering ample
opportunities for customization.

Example
-------
::

    from xapwrap import SmartIndex, Document, TextField, SortKey
    from datetime import date

    idx = SmartIndex('/tmp/index', True)
    d1 = Document(TextField('hi there bob'),
                  sortFields = [SortKey('date', date(2004, 1, 1)),
                                SortKey('author', 'Bob'),
                                SortKey('size', 450)])
    idx.index(d1)
    idx.close()

    idx = SmartIndex('/tmp/index')
    print idx.search('there', 'date', sortAscending = True)



Indices
-------

Important methods for C{ReadOnlyIndex}:
 __init__(self, *pathnames)
 close(self)
 configure(self, prefixMap = None, indexValueMap = None)
 flush(self)
 search(self, query, sortKeyt = None,
        startingIndex = 0, batchSize = MAX_DOCS_TO_RETURN,
        sortIndex = None, sortAscending = True,
        sortByRelevence = False)
 count(self, query)
 checkIndex(self, maxID)
 get_doccount(self, uid)

Important methods for C{Index}:
 (all methods in ReadOnlyIndex)
 __init__(self, pathname, create)
 index(self, doc)
 add_document(self, doc)
 replace_document(self, uid, doc)
 delete_document(self, uid)

C{SmartIndex} and C{SmartReadOnlyIndex} define the same methods as their
dumb counterparts.

The primary way to interact with a Xapian index is to use either the
C{Index} or C{ReadOnlyIndex} class. In addition to offering read only
access without the inconveniance of lock files, C{ReadOnlyIndex} offers
the ability to merge several xapian indices into one super index with
only a small performance impediement.

In addition to C{Index} and C{ReadOnlyIndex}, Xapwrap also offers
C{SmartIndex} and C{SmartReadOnlyIndex} classes. These classes
automatically store and manage the index value map and the prefix map in
the index. There are two caveats to using them however. First, one
cannot index documents that have a xapian ID of 1. Secondly, when using
C{SmartReadOnlyIndex} to combine multiple indices together, the indices
must have consistent value index maps. Indices where all documents have
the same index value map are always consistent. The problem only emerges
when indices can have different types of documents with different sets
of sort keys. More specifically, the problem can only emerge if one
indices documents in such a way that sort keys are added to different
indices in different orders.


Documents
---------

In order to add new data to an index, one asks a C{Index} or
C{SmartIndex} instance to index a C{Document} instance. Documents take a
sequence of text fields, a sequence of sort keys and a sequence of
keywords as constructor arguments. They also take optional universal
identifiers and an arbitrary serializable object. The first three
sequences can be created using the C{TextField}, C{SortKey}, and
C{Keyword} classes defined below. C{TextField} instances contain a chunk
of text and an optional name as well as a boolean indicating whether the
field is to be prefixed. Prefixed fields are effectively indexed twice:
after being indexed normally, each token is indexed again with the field
name. This allows the user to perform fielded searches and is primarily
useful for small text fields, such as the subject of an email or a list
of author names. C{Keyword} instances denote individual prefixed tokens
that are indexed with no positional information. C{SortKey} instances
denote arbitrary fields that are used for sorting documents. They
include a sort field name and the sort key value. Since Xapian only
accepts strings as sort keys, sort key values must be flattened into
strings before entering the index.

Xapwrap defines flattener functions that automatically flatten integer,
date, time, and datetime instances into strings that sort properly. You
can define your own flatteners for custom data types by using the
C{registerFlattener} class method of the C{Document} class.


Error Handling
--------------
Internal Xapian error conditions should generate normal python
exceptions defined in this file that inherit from xapwrap.XapianError.


Logging
-------
Xapwrap will use twisted's logging facilities if available. In any
event, a custom logging function can be supplied by setting xapwrap.log.


Future Work
-----------
Xapwrap currently does not support stemming or stop words, although a
future version will.

"""
try:
    set
except:
    from sets import Set as set

import cPickle, glob, os
import xapian
from document import makePairForWrite, StandardAnalyzer, Document, SortKey, Keyword
from document import UNICODE_ENCODING, UNICODE_ERROR_POLICY

try:
    from atop.tpython import FilesystemLock
except ImportError:
    try:
        from os import symlink, readlink, remove as rmlink
    except ImportError:
        import win32event

        class FilesystemLock:
            """A mutex

            A real mutex this time. See the non-win32 version for details.
            """

            locked = False
            clean = True

            def __init__(self, name):
                #Mutex name cannot contain backslash
                name = name.replace('\\', '/')
                self.name = name
                self._mutex = win32event.CreateMutex(None, False, name)
                if not self._mutex:
                    raise RuntimeError("Failed to create a named mutex")

            def lock(self):
                res = win32event.WaitForSingleObject(self._mutex, 0)
                self.locked = (res != win32event.WAIT_TIMEOUT)
                return self.locked

            def unlock(self):
                #C API ReleaseMutex version is supposed to return something to
                #tell whether the lock was correctly released or not. The binding
                #does not.
                win32event.ReleaseMutex(self._mutex)
                self.locked = False

    else:
        import errno

        class FilesystemLock:
            """A mutex.

            This relies on the filesystem property that creating
            a symlink is an atomic operation and that it will
            fail if the symlink already exists.  Deleting the
            symlink will release the lock.

            @ivar name: The name of the file associated with this lock.
            @ivar clean: Indicates whether this lock was released cleanly by its
            last owner.  Only meaningful after C{lock} has been called and returns
            True.
            """

            clean = None
            locked = False

            def __init__(self, name):
                self.name = name

            def lock(self):
                """Acquire this lock.

                @rtype: C{bool}
                @return: True if the lock is acquired, false otherwise.

                @raise: Any exception os.symlink() may raise, other than
                EEXIST.
                """
                try:
                    pid = readlink(self.name)
                except (OSError, IOError), e:
                    if e.errno != errno.ENOENT:
                        raise
                    self.clean = True
                else:
                    if not hasattr(os, 'kill'):
                        return False
                    try:
                        os.kill(int(pid), 0)
                    except (OSError, IOError), e:
                        if e.errno != errno.ESRCH:
                            raise
                        rmlink(self.name)
                        self.clean = False
                    else:
                        return False

                symlink(str(os.getpid()), self.name)
                self.locked = True
                return True

            def unlock(self):
                """Release this lock.

                This deletes the directory with the given name.

                @raise: Any exception os.readlink() may raise, or
                ValueError if the lock is not owned by this process.
                """
                pid = readlink(self.name)
                if int(pid) != os.getpid():
                    raise ValueError("Lock %r not owned by this process" % (self.name,))
                rmlink(self.name)
                self.locked = False

try:
    from twisted.python.log import msg as log
except ImportError:
    def log(*args):
        pass


# max number of bytes that can be indexed without forcing an index
# flush. this limits memory consumption
MAX_DATA_INDEXED_BETWEEN_FLUSHES = 200 * 1000

MAX_DOCS_TO_RETURN = 1000 * 1000

XAPIAN_LOCK_FILENAME = "db_lock"
XAPWRAP_LOCK_FILENAME = "xapian_lock"

# Xapian error handling is somewhat weak: all errors trigger either an
# IOError, a RuntimeError, or a ValueError. The exception's args
# attribute is a singleton tuple containing an explanation
# string. Possible errors include 'DatabaseCorruptError: Quartz metafile
# /tmp/foo/meta is invalid: magic string not found.' and
# 'DatabaseLockError: Unable to acquire database write lock
# /tmp/foo/db_lock'. Instead of looking inside exception error strings
# everywhere, I made a wrapper for xapian database operations that
# catches exceptions and translates them into the more meaningful
# exceptions shown below.

class XapianError(StandardError):
    pass
class XapianRuntimeError(XapianError):
    pass
class XapianLogicError(XapianError):
    pass
class XapianDatabaseError(XapianError):
    pass

class XapianAssertionError(XapianLogicError):
    pass
class InvalidOperationError(XapianLogicError):
    pass
class InvalidArgumentError(XapianLogicError):
    pass
class UnimplementedError(XapianLogicError):
    pass

class DocNotFoundError(XapianRuntimeError):
    pass
class RangeError(XapianRuntimeError):
    pass
class InternalError(XapianRuntimeError):
    pass
class FeatureUnavalableError(XapianRuntimeError):
    pass
class XapianNetworkError(XapianRuntimeError):
    pass

class NetworkTimeoutError(XapianNetworkError):
    pass

class DatabaseCorruptionError(XapianDatabaseError):
    pass
class DatabaseCreationError(XapianDatabaseError):
    pass
class DatabaseOpeningError(XapianDatabaseError):
    pass
class DatabaseLockError(XapianDatabaseError):
    pass
class DatabaseModifiedError(XapianDatabaseError):
    pass

# these exceptions are not Xapian errors
class UnknownDatabaseError(XapianError):
    pass

class NoIndexValueFound(XapianError):
    pass

class InconsistantIndex(XapianError):
    pass

class InconsistantIndexCombination(XapianError):
    pass


def makeTranslatedMethod(methodName):
    def translatedMethod(self, *args, **kwargs):
        try:
            return getattr(self.db, methodName)(*args, **kwargs)
        except (IOError, RuntimeError, ValueError), e:
            errorMsg = e.args[0]
            for subString, exceptionClass in self.exceptionStrMap.iteritems():
                if subString in errorMsg:
                    raise exceptionClass(e)
            else:
                raise UnknownDatabaseError(e)
        except:
            raise
    return translatedMethod

class ExceptionTranslater:
    def __init__(self, db):
        self.db = db

    def openIndex(klass, readOnly, *args, **kwargs):
        try:
            if readOnly:
                assert len(kwargs) == 0
                # assume all args are db paths
                db = xapian.Database(args[0])
                for path in args[1:]:
                    db.add_database(xapian.Database(path))
                return klass(db)
            else:
                try:
                    return klass(xapian.WritableDatabase(*args, **kwargs)) # for xapian 1.0+
                except AttributeError:
                    return klass(xapian.open(*args, **kwargs)) # for xapian 0.9.x
        except (IOError, RuntimeError, ValueError), e:
            errorMsg = e.args[0]
            for subString, exceptionClass in klass.exceptionStrMap.iteritems():
                if subString in errorMsg:
                    raise exceptionClass(e)
            else:
                raise UnknownDatabaseError(e)
        except Exception, e:
            raise UnknownDatabaseError(e)

    openIndex = classmethod(openIndex)

    # possible exceptions are taken from the list at
    # http://www.xapian.org/docs/apidoc/html/errortypes_8h.html
    exceptionStrMap = {
        # exceptions whose names differ between xapwrap and Xapian
        'DatabaseCorruptError': DatabaseCorruptionError,
        'AssertionError': XapianAssertionError,
        'DatabaseCreateError': DatabaseCreationError,

        # exceptions translated with the same name
        'DatabaseLockError': DatabaseLockError,
        'DatabaseOpeningError': DatabaseOpeningError,
        'DatabaseModifiedError': DatabaseModifiedError,
        'FeatureUnavalableError': FeatureUnavalableError,
        'DocNotFoundError': DocNotFoundError,
        'InvalidOperationError': InvalidOperationError,
        'InvalidArgumentError': InvalidArgumentError,
        'UnimplementedError': UnimplementedError,
        'NetworkError': XapianNetworkError,
        'NetworkTimeoutError': NetworkTimeoutError,
        'DatabaseError': XapianDatabaseError,
        'InternalError': InternalError,
        'RangeError': RangeError,
        'RuntimeError': XapianRuntimeError,
        'LogicError': XapianLogicError
        }

    get_doccount = makeTranslatedMethod('get_doccount')
    add_document = makeTranslatedMethod('add_document')
    replace_document = makeTranslatedMethod('replace_document')
    delete_document = makeTranslatedMethod('delete_document')
    flush = makeTranslatedMethod('flush')
    term_exists = makeTranslatedMethod('term_exists')
    reopen = makeTranslatedMethod('reopen')
    begin_transaction = makeTranslatedMethod('begin_transaction')
    commit_transaction = makeTranslatedMethod('commit_transaction')
    cancel_transaction = makeTranslatedMethod('cancel_transaction')
    get_lastdocid = makeTranslatedMethod('get_lastdocid')
    get_avlength = makeTranslatedMethod('get_avlength')
    get_termfreq = makeTranslatedMethod('get_termfreq')
    get_collection_freq = makeTranslatedMethod('get_collection_freq')
    get_doclength = makeTranslatedMethod('get_doclength')
    get_document = makeTranslatedMethod('get_document')

    postlist_begin = makeTranslatedMethod('postlist_begin')
    postlist_end = makeTranslatedMethod('postlist_end')
    termlist_begin = makeTranslatedMethod('termlist_begin')
    termlist_end = makeTranslatedMethod('termlist_end')
    positionlist_begin = makeTranslatedMethod('positionlist_begin')
    positionlist_end = makeTranslatedMethod('positionlist_end')
    allterms_begin = makeTranslatedMethod('allterms_begin')
    allterms_end = makeTranslatedMethod('allterms_end')


def makeProtectedDBMethod(method, setupDB = True):
    def protectedMethod(self, *args, **kwargs):
        if setupDB:
            self.setupDB()
        try:
            return method(self, *args, **kwargs)
##         # test that this works and doesn't recurse infinitely
##         except DatabaseModifiedError:
##             self.reopen()
##             return protectedMethod(self, *args, **kwargs)
        except XapianError, e:
            #log("error encountered while performing xapian index operation %s: %s"
            #    % (method.__name__, e))
            self.close()
            raise
    return protectedMethod


# there are lots of places below where we write code like:
# enq = mset = None
# try:
#     enq = self.enquire(foo)
#     mset = enq.get_mset(0, 10)
#     return mset[0][flimflam]
# except:
#     del enq, mset
#     raise

# the purpose of this code is to ensure that no references to enquire
# objects or msets will outlive the function call. msets and enquire
# objsects hold a reference to the xapian db, and thus prevent it from
# being properly gc'd. if we fail to delete enq and mset on exception,
# then they can be kept around for arbitrarily long periods of time as
# part of the exception state


# be extremely careful about keeping a db object in local scope;
# once its there, an unhandled exception could create a traceback
# containing a frame object that holds a copy of the locals dict,
# including the db object. if that frame/traceback object is kept
# around forever (which parts of twisted/quotient seem to do,
# especially deferreds), then the db object will never be deleted
# and the indexer lock will never go away.

# in order to prevent that from happening, we maintain two invariants:

# 1. the db is only accessed as an instance attribute and is never
# copied into a local variable. i.e., we always say self.db and
# never ever say db = self.db. this keeps the db object from ever
# getting captured by a frame/traceback.

# 2. the db is only accessed from within an exception handler that
# calls self.close() in the event of *any* failure. this ensures
# that the instance loses all references to the db on failure, so,
# even if the instance object is captured by a frame object (or
# something else), the db will already have been freed.


class ReadOnlyIndex:
    """
    I represent a Xapian index that is read only by wrapping the
    xapian.Database class. Because I provide read only access, I can be
    used to combine several Xapian indices into one index with
    performance only slightly lower than when using only one index.

    @cvar DEFAULT_QUERY_COMBINER_OP: the operation used by the query parser to combine query terms

    @cvar STEMMING_LANGUAGE: the language used by the query parser for
    stemming. this is of little use since Xapwrap does not yet support
    stemming when indexing.

    @ivar names: a sequence of file names representing paths to Xapian
    indices

    Please use the configure method to modify C{prefixMap} and C{indexValueMap}

    @ivar prefixMap: a map of prefixes used by named fields in the index
    and the name they should be referred to by the query parser

    @ivar indexValueMap: a map from sort field names to value integer

    @ivar amountIndexedSinceLastFlush: the number of bytes indexed since
    the last flush

    The following instance attributes should never be modified or
    accessed directly:

    @ivar db: the xapian index object
    @ivar qp: the xapian query parser object
    @ivar _searchSessions: a map from query description string to
    (enquire, lastIndexSortedBy)
    """

    DEFAULT_QUERY_COMBINER_OP = xapian.Query.OP_AND
    STEMMING_LANGUAGE = 'none'

    def __init__(self, *names):
        if len(names) < 1:
            raise ValueError("No index directory supplied to Index constructor")
        self.names = names
        self.db = None
        self.qp = None
        self._searchSessions = {}
        self.prefixMap = {}
        self.indexValueMap = {}
        self.amountIndexedSinceLastFlush = 0

    def setupDB(self):
        # we hide the db so that methods always access it only through
        # this method since db objects can be silently reaped when not
        # in use. db objects consume 5 file descriptors.

        if self.db is None:
            self._setupDB()

            #self.qp = xapian.QueryParser()
            # this is vital: these options specify no language for
            # stemming (""), disable stemming (False), and specify an
            # empty stop word object (None). we need this because by
            # default, xapian's query parser does english stemming
            #s = xapian.Stem(self.STEMMING_LANGUAGE)
            #self.qp.set_stemmer(s)

            # we want query terms to be ANDed together by default
            #self.qp.set_default_op(self.DEFAULT_QUERY_COMBINER_OP)
            self._configure()

            log("Index %s contains %s documents" %
                (self.names, self.get_doccount()))

    def _setupDB(self):
        self.db = ExceptionTranslater.openIndex(True, *self.names)

    def close(self):
        log("closing xapian index %s" % self.names)
        for query in self._searchSessions.keys():
            del self._searchSessions[query]
        self.qp = None
        self.db = None

    def _configure(self):
        if 'uid' not in self.indexValueMap:
            # this a gross hack...
            self.indexValueMap['uid'] = 0
            self.indexValueMap['uidREV'] = 1
        if self.qp is not None:
            for k, v in self.prefixMap.iteritems():
                # check for unicode encoding?
                if v:
                    V = v.upper()
                else:
                    V = k.upper()
                self.qp.add_prefix(k, V)

    def configure(self, prefixMap = None, indexValueMap = None):
        if prefixMap is not None:
            self.prefixMap = prefixMap
        if indexValueMap is not None:
            self.indexValueMap = indexValueMap
        self._configure()

    def get_doccount(self):
        return self.db.get_doccount()
    get_doccount = makeProtectedDBMethod(get_doccount)

    def enquire(self, query):
        searchSession = None
        try:
            searchSession = xapian.Enquire(self.db.db)
            searchSession.set_query(query)
            return searchSession
        except:
            del query, searchSession
            raise
    enquire = makeProtectedDBMethod(enquire)

    def flush(self):
        if self.db is not None:
            self.db.flush()
            self.amountIndexedSinceLastFlush = 0
    flush = makeProtectedDBMethod(flush)

    def search(self, query,
               sortKey = None,
               startingIndex = 0,
               batchSize = MAX_DOCS_TO_RETURN,
               sortIndex = None, sortAscending = True,
               sortByRelevence = False,
               valuesWanted = None,
               collapseKey = None):
        """
        Search an index.

        @ivar valuesWanted: a list of Values that will be returned as part
        of the result dictionary.
        """

        # TODO - allow a simple way to get Keywords out
        self.setupDB()
        if isinstance(query, (str, unicode)):
            query = ParsedQuery(query)
        elif not(isinstance(query, Query)):
            raise ValueError("query %s must be either a string or a "
                             "subclass of xapwrap.Query" % query)

        q = query.prepare(self.qp)
        # uggg. this mess is due to the fact that xapain Query objects
        # don't hash in a sane way.
        try:
            qString = q.get_description() # deprecated since xapian 1.0, removal in 1.1
        except AttributeError:
            qString = str(q)

        # the only thing we use sortKey for is to set sort index
        if sortKey is not None:
            sortIndex = self.indexValueMap[sortKey]
        if collapseKey is not None:
            collapseKey = self.indexValueMap[collapseKey]

        # once you call set_sorting on an Enquire instance, there is no
        # way to resort it by relevence, so we have to open a new
        # session instead.

        # ignore sortAscending since there's no easy way to implement
        # ascending relevancy sorts and it's tough to imagine a case
        # where you'd want to see the worst results. in any event, the
        # user can always sort by relevancy and go to the last page of
        # results.

        enq = mset = None
        if qString not in self._searchSessions:
            self._searchSessions[qString] = (self.enquire(q), None)
        try:
            enq, lastIndexSortedBy = self._searchSessions[qString]

            # if we don't set sortIndex, the results will be returned
            # sorted by relevance, assuming that we have never called
            # set_sorting on this session
            if sortByRelevence and lastIndexSortedBy is not None:
                sortIndex = sortKey = None
                if lastIndexSortedBy is not None:
                    del self._searchSessions[qString]
                    self._searchSessions[qString] = (self.enquire(q), None)
                    enq, lastIndexSortedBy = self._searchSessions[qString]
            if sortByRelevence is not None and sortIndex is not None:
                enq.set_sort_by_relevance_then_value(sortIndex, not sortAscending)
            elif sortIndex is not None:
                # It seems that we have the opposite definition of sort ascending
                # than Xapian so we invert the ascending flag!
                enq.set_sort_by_value(sortIndex, not sortAscending)

            if collapseKey is not None:
                enq.set_collapse_key(collapseKey)

            self._searchSessions[qString] = (enq, sortIndex)

            mset = enq.get_mset(startingIndex, batchSize)
            results = []
            for m in mset:
                thisResult = {}
                thisResult['uid'] = m[xapian.MSET_DID]
                thisResult['score'] = m[xapian.MSET_PERCENT]
                if valuesWanted:
                    xapDoc = m[4]
                    valRes = {}
                    for valName in valuesWanted:
                        valueIndex = self.indexValueMap.get(valName, None)
                        if valueIndex is None:
                            raise NoIndexValueFound(valName, self.indexValueMap)
                        valRes[valName] = xapDoc.get_value(valueIndex)
                    thisResult['values'] = valRes
                results.append(thisResult)
            return enq, mset, results
        except:
            del enq, mset
            raise
    search = makeProtectedDBMethod(search)

    def count(self, query):
        enq = mset = None
        try:
            enq = self.enquire(query)
            # get_matches_estimated does not return accurate results if
            # given a small ending number like 0 or 1
            mset = enq.get_mset(0, MAX_DOCS_TO_RETURN)
            sizeEstimate = mset.get_matches_estimated()
            return sizeEstimate, self.get_doccount()
        except:
            del enq, mset
            raise
    count = makeProtectedDBMethod(count)

    def checkIndex(self, maxID):
        """Compute a list of all UIDs less than or equal to maxID that
        are not in the db.
        """
        # I had originally suspected that the performance hit of
        # returning a huge list in the case of empty indexes would be
        # substantial, but testing with a 120,000 msg index indicates
        # that performance is fine and that the space overhead is quite
        # reasonable. If that were not the case, this could be optimized
        # by calculating the maximum document ID in the index and only
        # scanning up to the minimum of maxID and the max ID in the
        # index, assuming that were using the same document IDs in the
        # index as in atop.

        missingUIDs = []
        for uid in xrange(maxID + 1):
            term = makePairForWrite('UID', str(uid))
            if not self.db.term_exists(term):
                missingUIDs.append(uid)
        return missingUIDs
    checkIndex = makeProtectedDBMethod(checkIndex)

    def get_documents(self, uid):
        """ return a list of remapped UIDs corresponding to the actual UID given
        """
        docTerm = makePairForWrite('UID', str(uid))
        candidates = self.search(RawQuery(docTerm))
        return [int(c['uid']) for c in candidates]

    def get_document(self, uid):
        # we cannot simply use db.get_document since doc ids get
        # remapped when combining multiple databases
        candidates = self.get_documents(uid)
        if len(candidates) == 0:
            raise DocNotFoundError(uid)
        elif len(candidates) == 1:
            return self._get_document(candidates[0])
        else:
            raise InconsistantIndex(
                "Something has gone horribly wrong. I tried "
                "retrieving document id %s but found %i documents "
                "with that document ID term" % (uid, len(candidates)))

    def _get_document(self, uid):
        assert isinstance(uid, int)
        return self.db.get_document(uid)
    _get_document = makeProtectedDBMethod(_get_document)

    def term_exists(self, term):
        assert isinstance(term, str)
        return self.db.term_exists(term)
    term_exists = makeProtectedDBMethod(term_exists)

    def get_lastdocid(self):
        return self.db.get_lastdocid()
    get_lastdocid = makeProtectedDBMethod(get_lastdocid)

# XXX FIXME: we should consider deleting all searchSessions whenever we
# add a document, or we should reopen the db


class Index(ReadOnlyIndex):

    def __init__(self, name, create = False, analyzer = None):
        # XXX FIXME: we should really try opening the db here, so that
        # any errors are caught immediately rather than waiting for the
        # first time we try to do something...
        ReadOnlyIndex.__init__(self, name)
        self.name = name
        if create:
            self.flags = xapian.DB_CREATE_OR_OPEN
        else:
            self.flags = xapian.DB_OPEN
        self.analyzer = analyzer or StandardAnalyzer()
        self.lockFile = FilesystemLock(
            os.path.join(self.name, XAPWRAP_LOCK_FILENAME))

    def _setupDB(self):
        """ really get a xapian database object """

        # xapian expects directories! self.name should refer to a
        # directory. if it doesn't exist, we'll make one.
        if not os.path.exists(self.name):
            os.mkdir(self.name)

        # try to acquire a lock file
        if not self.lockFile.lock():
            owningPid = os.readlink(self.lockFile.name)
            errorMsg = ("cannot acquire lock file for xapian index %s"
                        "because it is owned by process %s" %
                        (self.name, owningPid))
            log(errorMsg)
            raise DatabaseLockError(errorMsg)
        xapLockFilePath = os.path.join(self.name, XAPIAN_LOCK_FILENAME)
        if os.path.exists(xapLockFilePath):
            log("Stale database lock found in %s. Deleting it now." % xapLockFilePath)
            os.remove(xapLockFilePath)

        # actually try to open a xapian DB
        try:
            try:
                self.db = ExceptionTranslater.openIndex(False, self.name, self.flags)
            except DatabaseCorruptionError, e:
                # the index is trashed, so there's no harm in blowing it
                # away and starting from scratch
                log("Xapian index at %s is corrupted and will be destroyed"
                    % self.name)
                if self.lockFile.locked:
                    self.lockFile.unlock()
                for idxFname in glob.glob(os.path.join(self.name, '*')):
                    os.remove(idxFname)
                self.db = ExceptionTranslater.openIndex(False, self.name, self.flags)
        finally:
            if self.db is None and self.lockFile.locked:
                self.lockFile.unlock()

    def __del__(self):
        self.close()

    def close(self):
        # this is important! the only way to get xapian to release the
        # db lock is to call the db object's destructor. that won't
        # happen until nobody is holding a reference to the db
        # object. unfortunately, the query parser holds a reference to
        # it, so the query parser must also go away. do not hold
        # references to these objects anywhere but here.

        # enquire objects and mset objects hold a reference to the db,
        # so if any of them are left alive, the db will not be reclaimed

        if self.db is not None:
            ReadOnlyIndex.close(self)
            # the islink test is needed in case the index directory has
            # been deleted before we close was called.
            if self.lockFile.locked and os.path.islink(self.lockFile.name):
                self.lockFile.unlock()
            # there is no point in checking if the lock file is still
            # around right here: it will only be deleted when xapian's
            # destructor runs, but python defers running destructors
            # until after exception handling is complete. since this
            # code will often get called from an exception handler, we
            # have to assume that the lock file's removal will be
            # delayed at least until after this method exits

    def get_document(self, uid):
        return self._get_document(uid)

    # methods that modify db state

    def index(self, doc):
        self.setupDB()
        if hasattr(doc, 'uid') and doc.uid:
            uid = int(doc.uid)
            doc.sortFields.append(SortKey('uid', uid))
            doc.keywords.append(Keyword('uid', str(uid)))
            xapDoc = doc.toXapianDocument(self.indexValueMap, self.prefixMap)
            self.replace_document(uid, xapDoc)
        else:
            # We need to know the uid of the doc we're going to add
            # before we add it so we can setup appropriate uid sorting
            # values. But, another thread could potentially insert a
            # document at that uid after we determine the last uid, but
            # before we manage the insertion. Yay race conditions! So we
            # try to add the document and then check that it ended up at
            # the right uid. If it did not, we update it with the
            # correct uid sort values.
            uid = self.get_lastdocid() + 1
            doc.sortFields.append(SortKey('uid', uid))
            doc.keywords.append(Keyword('uid', str(uid)))
            xapDoc = doc.toXapianDocument(self.indexValueMap, self.prefixMap)
            newUID = self.add_document(xapDoc)
            if newUID != uid:
                doc.sortFields.append(SortKey('uid', newUID))
                doc.keywords.append(Keyword('uid', str(newUID)))
                xapDoc = doc.toXapianDocument(self.indexValueMap, self.prefixMap)
                self.replace_document(newUID, xapDoc)

            # a simpler alternative would be to add an empty document
            # and then replace it. the problem with that strategy is
            # that it kills performance since xapian performs an
            # implicit flush when you replace a document that was added
            # but not yet committed to disk.

        self.amountIndexedSinceLastFlush += len(doc)
        if self.amountIndexedSinceLastFlush > MAX_DATA_INDEXED_BETWEEN_FLUSHES:
            self.flush()
        return uid

    def add_document(self, doc):
        return self.db.add_document(doc)
    add_document = makeProtectedDBMethod(add_document)

    def replace_document(self, uid, doc):
        return self.db.replace_document(uid, doc)
    replace_document = makeProtectedDBMethod(replace_document)

    def delete_document(self, docID):
        return self.db.delete_document(docID)
    delete_document = makeProtectedDBMethod(delete_document)

class Query:
    pass

class ParsedQuery(Query):
    def __init__(self, queryString):
        if isinstance(queryString, unicode):
            queryString = queryString.encode(UNICODE_ENCODING, UNICODE_ERROR_POLICY)
        # as of xapian 0.9.5 the query parser makes trouble with utf-8. but it
        # also doesnt work with iso-8859-15, so we just live with ascii-only search
        # for now... - a utf8 fix seems to be planned for the near future!
        self.queryString = queryString

    def prepare(self, queryParser):
        return queryParser.parse_query(self.queryString)

class RawQuery(Query):
    def __init__(self, queryString):
        if isinstance(queryString, unicode):
            queryString = queryString.encode('utf-8')

        assert isinstance(queryString, str)
        self.queryString = queryString

    def prepare(self, queryParser):
        return xapian.Query(self.queryString)

class QObjQuery(Query):
    def __init__(self, query):
        assert isinstance(query, xapian.Query)
        self.query = query

    def prepare(self, queryParser):
        return self.query

class SmartIndex(Index):
    documentFactory = Document

    def __init__(self, *args, **kwargs):
        Index.__init__(self, *args, **kwargs)
        self.fetchState()

    def saveState(self):
        self.setupDB()
        state = {'indexValueMap': self.indexValueMap,
                 'prefixMap': self.prefixMap}
        d = self.documentFactory(uid = 1, data = state)
        self.index(d, checkID = False)
        self.flush()

    def fetchState(self):
        self.setupDB()
        if self.get_doccount() == 0:
            # Don't rely on the try:except: for this case
            self.saveState()
        try:
            doc = self.get_document(1)
        except DocNotFoundError:
            newState = {'indexValueMap': {}, 'prefixMap': {}}
            self.saveState()
        else:
            dataStr = doc.get_data()
            newState = cPickle.loads(dataStr)
        self.indexValueMap.update(newState['indexValueMap'])
        self.prefixMap.update(newState['prefixMap'])

    def index(self, doc, checkID = True):
        if hasattr(doc, 'uid') and doc.uid == 1 and checkID:
            raise InvalidArgumentError(
                "document UIDs must be greater than one when using SmartIndex")

        docSortKeys = set([sk.name for sk in doc.sortFields if sk.name is not None])
        indexSortKeys = set(self.indexValueMap.keys())
        if not docSortKeys.issubset(indexSortKeys):
            nextValueIndex = 1 + max(self.indexValueMap.itervalues())
            # we sort the sortKeys in order to improve the odds that two
            # indices that are indexed with the same documents in the
            # same order will always end up with the same
            # indexValueMaps, even if different versions of python are
            # used with different hash functions
            sortKeys = list(docSortKeys)
            sortKeys.sort()
            for sortKey in sortKeys:
                if sortKey not in self.indexValueMap:
                    assert nextValueIndex % 2 == 0
                    self.indexValueMap[sortKey] = nextValueIndex
                    self.indexValueMap[sortKey + 'REV'] = nextValueIndex + 1
                    nextValueIndex += 2
            self.saveState()

        docKeywords = set([tf.name for tf in doc.textFields if tf.prefix] +
                               [kw.name for kw in doc.keywords])
        indexKeyWords = set(self.prefixMap.keys())
        if not docKeywords.issubset(indexKeyWords):
            for k in docKeywords - indexKeyWords:
                self.prefixMap[k] = k.upper()
            self.saveState()

        return Index.index(self, doc)


class SmartReadOnlyIndex(ReadOnlyIndex):

    def __init__(self, *args, **kwargs):
        ReadOnlyIndex.__init__(self, *args, **kwargs)
        self.fetchState()

    def fetchState(self):
        stateDocIDs = self.get_documents(1)
        stateDocs = map(self._get_document, stateDocIDs)
        states = [cPickle.loads(s.get_data()) for s in stateDocs]

        # should we issue a warning when the number of states that we
        # retrieve is less than the number of indices we opened? the
        # only problem is that some indices may be empty, but there's no
        # easy way to check how many documents are in a subindex without
        # opening it explicitly using xapian.Database and that seems
        # rather expensive for this code path.

        # merge all the states into a master state
        master = {'prefixMap': self.prefixMap,
                  'indexValueMap': self.indexValueMap}
        # note that if there are conflicts, there is no guarantee on who
        # will win, but it doesn't matter since we'll die on conflicts
        # later anyway
        for s in states:
            for substate in ('prefixMap', 'indexValueMap'):
                sub = s.get(substate, {})
                mSub = master[substate]
                for k, v in sub.iteritems():
                    mSub[k] = v

        # ensure that states are compatible (check for conflicts)
        conflicts = []
        for s in states:
            for substate in ('prefixMap', 'indexValueMap'):
                sub = s.get(substate, {})
                mSub = master[substate]
                for k, v in sub.iteritems():
                    if k in mSub and mSub[k] != v:
                        # we defer error reporting so that the user sees
                        # as much info on the error as possible
                        conflicts.append((substate, k, v, mSub[k]))

        # the only way states can be incompatible is if two states have
        # different values for the same keys in the same substate

        if conflicts:
            raise InconsistantIndexCombination(
                "The SmartReadOnlyIndex opened on %s cannot recconcile "
                "the following conflicts in the subindices' states:\n%s"
                % (self.names,
                   '\n'.join(["%s[%r] is %r in one index but %r in another"
                              % c for c in conflicts])))

        self.prefixMap = master['prefixMap']
        self.indexValueMap = master['indexValueMap']

    def search(self, query, sortKey = None,
               startingIndex = 0,
               batchSize = MAX_DOCS_TO_RETURN,
               sortIndex = None, sortAscending = True,
               sortByRelevence = False):
        # if the appropriate index value string is not in
        # self.indexValueMap, fetchState() before calling
        # ReadOnlyIndex.search. if it still isn't there, let
        # ReadOnlyIndex.search take care of throwing an error
        if sortKey is not None and sortKey not in self.indexValueMap:
            self.fetchState()
        return ReadOnlyIndex.search(self, query, sortKey,
                                    startingIndex, batchSize,
                                    sortIndex, sortAscending,
                                    sortByRelevence)

