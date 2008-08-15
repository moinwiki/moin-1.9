"""
    xapwrap.document - Pythonic wrapper around Xapian's Document API
"""
import datetime
import re
import cPickle
import xapian

MAX_KEY_LEN = 240 # this comes from xapian's btree.h, Btree::max_key_len
# NOTE: xapian's btree.h file says that its actually 252, but due to
# xapian's implementation details, the actual limit is closer to 245
# bytes. See http://thread.gmane.org/gmane.comp.search.xapian.cvs/329
# for more info, especially the second message.

# The limit described above only holds true assuming keys that do not
# contain any NULL bytes. Since xapian internally escapes \0 bytes,
# xapian sees the key length as (2*N + 2) where N is the number of
# embedded NULL characters.

INTER_FIELD_POSITION_GAP = 100

UNICODE_ENCODING = "UTF-8" # XXX this should not be hardcoded on module level
UNICODE_ERROR_POLICY = "replace"

class StandardAnalyzer:
    WORD_RE = re.compile('\\w{1,%i}' % MAX_KEY_LEN, re.U)

    def tokenize(self, unknownText):
        originalText = cleanInputText(unknownText, True)
        # we want to perform lower() and the re search using a unicode
        # object. if we try to perform those operations on regular
        # string object that happens to represent unicode text encoded
        # with UTF-8, we'll get garbage, or at least an
        # OS/libc/$LC_CTYPE dependant result
        text = originalText.lower()
        for match in self.WORD_RE.finditer(text):
            # we yield unicode ONLY
            yield match.group()


class TextField(object):
    __slots__ = ('name', 'text', 'prefix')

    def __init__(self, name, text = '', prefix = False):
        if name and not text:
            assert not prefix  # it makes no sense to use a prefixed
                               # field without a name
            self.text = name
            self.name = ''
        else:
            self.name = name
            self.text = text
        self.prefix = prefix

    def __len__(self):
        return len(self.text)

class SortKey(object):
    __slots__ = ('name', 'value', 'index', 'flattener')

    def __init__(self, name, value, index = None, flattener = None):
        self.name = name
        self.value = value
        self.index = index
        assert (name is None) ^ (index is None)
        self.flattener = flattener

class Value(SortKey):
    pass

class Term(object):
    __slots__ = ('value')

    def __init__(self, value):
        self.value = value

    def __len__(self):
        return len(self.value)

class Keyword(object):
    __slots__ = ('name', 'value')

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __len__(self):
        return len(self.value)


class Document:
    """
    @ivar keywords: sequence of Keyword objects
    @ivar sortFields: sequence of SortKey objects
    @ivar textFields: sequence of TextField objects

    @cvar analyzerFactory: factory object for constructing analyzers
    @cvar _picklerProtocol: protocol used in pickling data attributes
    @cvar _noObject: dummy object used to indicate that there is no
    data attribute
    @cvar source: this is an optional argument to point at the
    original text/object that this document represents
    """
    _noObject = object()
    _picklerProtocol = -1
    analyzerFactory = StandardAnalyzer

    # XXX TODO: add a fromXapianDoc classmethod that can be used by
    # indices when returning documents from the db

    def __init__(self, textFields = (), sortFields = (), keywords = (),
                 terms = (), values = (), uid = None, data = _noObject, source = None):
        """
        sortFields and values are really the same thing as far as
        xapian is concerned. We differentiate them in the hope of
        making the API easier to understand.
        """
        for fields in ('textFields', 'sortFields', 'keywords', 'terms', 'values'):
            arg = vars()[fields]
            if not isinstance(arg, (list, tuple)):
                arg = (arg,)
            setattr(self, fields, list(arg))
            # copy the list so we can modify without affecting the original
        self.uid = uid
        self.data = data
        self.source = source
        # sortFields and values are really the same thing as far as xapian is concerned
        self.sortFields += self.values

    def __len__(self):
        length = 0
        for fieldList in (self.textFields, self.keywords):
            length += sum(map(len, fieldList))

        if self.data != self._noObject:
            length += len(cPickle.dumps(self.data, self._picklerProtocol))

        return length

    def toXapianDocument(self, indexValueMap, prefixMap=None):
        d = xapian.Document()
        position = 0
        analyzer = self.analyzerFactory()

        # add text fields
        for field in self.textFields:
            # XXX: terms textFields won't get numbered
            # after each other, needed for titles
            position = 0
            for token in analyzer.tokenize(field.text):
                if isinstance(token, tuple):
                    token, position = token
                else:
                    position += 1
                # the xapian swig bindings don't like unicode objects, so we
                # decode terms to UTF-8 before indexing. this is fine as
                # long as all data that goes into the db (whether for
                # indexing or search) is converted to UTF-8 string and all
                # data coming from the db (.get_value(), .get_data()) is
                # decoded as UTF-8.
                token = token.encode(UNICODE_ENCODING, UNICODE_ERROR_POLICY)
                # the tokenizer cannot guarantee that token length is
                # below MAX_KEY_LEN since the regexp is done with
                # unicode and the result is later converted to UTF-8. In
                # the process, the string length could expand, so we
                # need to check here as well.
                d.add_posting(checkKeyLen(token), position)
            #position += INTER_FIELD_POSITION_GAP

            if field.prefix:
                prefix = field.name
                for token in analyzer.tokenize(field.text):
                    if isinstance(token, tuple):
                        token, position = token
                    else:
                        position += 1
                    # token is unicode, but gets converted to UTF-8
                    # by makePairForWrite:
                    term = makePairForWrite(prefix, token, prefixMap)
                    d.add_posting(term, position)
                #position += INTER_FIELD_POSITION_GAP

        # add keyword fields
        for field in self.keywords:
            term = makePairForWrite(field.name, field.value, prefixMap)
            d.add_term(term)

        # add non positional terms
        for term in self.terms:
            d.add_term(term.value)

        # add sort keys
        for field in self.sortFields:
            self.addSortField(d, field, indexValueMap)

        # serialize and add the data object if present
        if self.data is not self._noObject:
            dataStr = cPickle.dumps(self.data, self._picklerProtocol)
            d.set_data(dataStr)

        return d

    def addSortField(self, doc, field, indexValueMap):
        if field.index is None:
            valueIndex = indexValueMap.get(field.name, None)
            if valueIndex is None:
                from index import NoIndexValueFound
                raise NoIndexValueFound(field.name, indexValueMap)
        else:
            valueIndex = field.index
        assert isinstance(valueIndex, int)

        if field.flattener:
            flatValue = field.flattener(field.value)
        else:
            flatValue = self.flatten(field.value)
        # xapian has no limit on value length
        cleanValue = cleanInputText(flatValue)
        doc.add_value(valueIndex, cleanValue)

    _flatteners = {}

    def flatten(self, value):
        t = type(value)
        if t == str:
            return value
        elif t in self._flatteners:
            flattener = self._flatteners[t]
            flatVal = flattener(value)
            return flatVal
        else:
            raise ValueError("Cannot flatten %r into a string. Perhaps you "
                             "should register a flattener for type %r."
                             % (value, type(value)))

    def registerFlattener(klass, typeToFlatten, flattener):
        if typeToFlatten in klass._flatteners:
            raise ValueError("A sort field flattener for type %s has already"
                             "been registered (%s) but you are attempting to"
                             "register a new flattener: %s"
                             % (typeToFlatten, klass._flatteners[typeToFlatten],
                                flattener))
        assert callable(flattener)
        klass._flatteners[typeToFlatten] = flattener
    registerFlattener = classmethod(registerFlattener)

    def unregisterFlattener(klass, typeToFlatten):
        if typeToFlatten in klass._flatteners:
            del klass._flatteners[typeToFlatten]
    unregisterFlattener = classmethod(unregisterFlattener)

# common flatteners:

def flattenNumeric(value, numDigits = 10):
    return ''.join(('%', str(numDigits), '.d')) % value

Document.registerFlattener(int, flattenNumeric)

def flattenLong(value):
    return flattenNumeric(value, numDigits=20)

Document.registerFlattener(long, flattenLong)

def flattenDate(value):
    return value.isoformat()

for dt in (datetime.date, datetime.time, datetime.datetime):
    Document.registerFlattener(dt, flattenDate)

def flattenUnicode(value):
    return value.encode(UNICODE_ENCODING)

Document.registerFlattener(unicode, flattenUnicode)


def cleanInputText(unknownText, returnUnicode = False):
    if isinstance(unknownText, str):
        originalText = unknownText.decode(UNICODE_ENCODING, UNICODE_ERROR_POLICY) # XXX hardcoded UTF-8, make param XXX
    elif isinstance(unknownText, unicode):
        originalText = unknownText
    else:
        raise ValueError("Only strings and unicode objects can be indexed.")
    # be very careful about lowercasing the text here: since the API we
    # expose to higher levels doesn't allow searchup.py to call
    # findInField directly, searches for INDEXERVERSION:4 have to be
    # sent as regular queries. lowercasing all queries here will break
    # keyword searches.
    if returnUnicode:
        return originalText
    else:
        return originalText.encode(UNICODE_ENCODING, UNICODE_ERROR_POLICY)


def makePairForWrite(prefix, token, prefixMap=None):
    # prefixes must be uppercase; if the prefix given to us is a str
    # that happens to be UTF-8 encoded, bad things will happen when we
    # uppercase it, so we convert everything to unicode first
    if isinstance(prefix, str):
        prefix = prefix.decode(UNICODE_ENCODING, UNICODE_ERROR_POLICY)
    if isinstance(token, str):
        token = token.decode(UNICODE_ENCODING, UNICODE_ERROR_POLICY) # XXX hardcoded UTF-8, make param

    if prefixMap is None:
        prefix = prefix.upper()
    else: # we have a map, so first translate it using the map (e.g. 'title' -> 'S')
        prefix = prefixMap.get(prefix, prefix.upper())

    result = '%s%s%s' % (prefix, prefix[0] == 'X' and ':' or '', token)
    # since return value is going into the db, it must be encoded as UTF-8
    result = result.encode(UNICODE_ENCODING, UNICODE_ERROR_POLICY)
    return checkKeyLen(result)

def checkKeyLen(s):
    if not s:
        return ' '
    numNullBytes = s.count('\0') + 1
    xapianLen = numNullBytes + len(s) + 1 # that last one is for the
                                          # terminating \0
    if xapianLen < MAX_KEY_LEN:
        return s
    else:
        # doing nothing seems preferable to mangling an overly large
        # token that we don't know how to handle. we use a space
        # instead of an empty string because xapian doesn't like
        # getting empty strings added as terms
        return ' '

