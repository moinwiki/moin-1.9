# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Internationalization

    This subpackage controls the access to the language modules
    contained in it. Each language is in a module with a dictionary
    storing the original texts as keys and their translation in the
    values. Other supporting modules start with an underscore.

    Public attributes:
    languages -- languages that MoinMoin knows about
    NAME, ENCODING, DIRECTION, MAINTAINER -- named indexes

    Public functions:
    filename(lang) -- return the filename of lang
    loadLanguage(request, lang) -- load text dictionary for a specific language, returns (formatted, unformatted)
    requestLanguage(request, usecache=1) -- return the request language
    wikiLanguages() -- return the available wiki user languages
    browserLanguages() -- return the browser accepted languages
    getDirection(lang) -- return the lang direction either 'ltr' or 'rtl'
    getText(str, request) -- return str translation
    canRecode(input, output, strict) -- check recode ability
    
    @copyright: 2001-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os

try:
    import cPickle as pickle
except ImportError:
    import pickle

# Set pickle protocol, see http://docs.python.org/lib/node64.html
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL

from MoinMoin import config
from MoinMoin.Page import Page

NAME, ENAME, ENCODING, DIRECTION, MAINTAINER = range(0,5)
# we do not generate this on the fly due to performance reasons -
# importing N languages would be slow for CGI...
from meta import languages

# This is a global for a reason: in persistent environments all
# languages in use will be cached; Note: you have to restart if you
# update language data in such environments.  
_text_cache = {}

# also cache the unformatted strings...
_unformatted_text_cache = {}

# remember what has been marked up correctly already
_done_markups = {}

def filename(lang):
    """
    Return the filename for lang

    This is not always the same as the language name. This function hides
    the naming details from the clients.
    """
    filename = lang.replace('-', '_')
    filename = filename.lower()
    return filename

def formatMarkup(request, text, currentStack = []):
    """
    Formats the text passed according to wiki markup.
    This raises an exception if a text needs itself to be translated,
    this could possibly happen with macros.
    """
    try:
        currentStack.index(text)
        raise Exception("Formatting a text that is being formatted?!")
    except ValueError:
        pass
    currentStack.append(text)

    from MoinMoin.Page import Page
    from MoinMoin.parser.wiki import Parser
    from MoinMoin.formatter.text_html import Formatter
    import StringIO

    origtext = text
    out = StringIO.StringIO()
    request.redirect(out)
    parser = Parser(text, request, line_anchors=False)
    formatter = Formatter(request, terse = True)
    reqformatter = None
    if hasattr(request, 'formatter'):
        reqformatter = request.formatter
    request.formatter = formatter
    p = Page(request, "$$$$i18n$$$$")
    formatter.setPage(p)
    parser.format(formatter)
    text = out.getvalue()
    if reqformatter == None:
        del request.formatter
    else:
        request.formatter = reqformatter
    request.redirect()
    del currentStack[-1]
    text = text.strip()
    return text
   
def loadLanguage(request, lang):
    """
    Load text dictionary for a specific language.

    Note that while ISO language coded use a dash, like 'en-us', our
    languages files use '_' like 'en_us' because they are saved as
    Python source files.

    Raises an exception if this method is called from within itself
    (by the formatter). In that case, the translation file is buggy.
    Possible causes are having a text that is interpreted to again
    need a text in the same language. That means you cannot use
    the GetText macro in translated strings, nor any wiki markup
    that requires translated strings (eg. "attachment:").

    """
    from MoinMoin import caching
    cache = caching.CacheEntry(request, arena='i18n', key=lang)
    langfilename = os.path.join(os.path.dirname(__file__), filename(lang) + '.py')
    needsupdate = cache.needsUpdate(langfilename)
    if not needsupdate:
        try:
            (uc_texts, uc_unformatted) = pickle.loads(cache.content())
        except (IOError,ValueError,pickle.UnpicklingError): #bad pickle data, no pickle
            needsupdate = 1

    if needsupdate:    
        from MoinMoin.util import pysupport
        lang_module = "MoinMoin.i18n." + filename(lang)
        texts = pysupport.importName(lang_module, "text")
        if not texts:
            return (None, None)
        meta = pysupport.importName(lang_module, "meta") 
        encoding = meta['encoding']

        # convert to unicode
        uc_texts = {}
        for idx in texts:
            uidx = idx.decode(encoding)
            utxt = texts[idx].decode(encoding)
            uc_texts[uidx] = utxt
        uc_unformatted = uc_texts.copy()

        # is this already on wiki markup?
        if meta.get('wikimarkup', False):
            # use the wiki parser now to replace some wiki markup with html
            text = ""
            global _done_markups
            if not _done_markups.has_key(lang):
                _done_markups[lang] = 1
                for key in uc_texts:
                    text = uc_texts[key]
                    uc_texts[key] = formatMarkup(request, text)
                _done_markups[lang] = 2
            else:
                if _done_markups[lang] == 1:
                    raise Exception("Cyclic usage detected; you cannot have translated texts include translated texts again! "
                                    "This error might also occur because of things that are interpreted wiki-like inside translated strings. "
                                    "This time the error occurred while formatting %s." % text)
        cache.update(pickle.dumps((uc_texts, uc_unformatted), PICKLE_PROTOCOL))

    return (uc_texts, uc_unformatted)


def requestLanguage(request):
    """ 
    Return the user interface language for this request.
    
    The user interface language is taken from the user preferences for
    registered users, or request environment, or the default language of
    the wiki, or English.

    This should be called once per request, then you should get the
    value from request object lang attribute.
    
    Unclear what this means: "Until the code for get
    text is fixed, we are caching the request language locally."

    @param request: the request object
    @keyword usecache: whether to get the value form the local cache or
                       actually look for it. This will update the cache data.
    @rtype: string
    @return: ISO language code, e.g. 'en'
    """

    # Return the user language preferences for registered users
    if request.user.valid and request.user.language:
        return request.user.language

    # Or try to return one of the user browser accepted languages, if it
    # is available on this wiki...
    available = wikiLanguages()
    for lang in browserLanguages(request):
        if available.has_key(lang):
            if request.http_accept_language:
                request.setHttpHeader('Vary: Accept-Language')
            return lang
    
    # Or return the wiki default language...
    if available.has_key(request.cfg.default_lang):
        lang = request.cfg.default_lang

    # If everything else fails, read the manual... or return 'en'
    else:
        lang = 'en'

    return lang


def wikiLanguages():
    """
    Return the available user languages in this wiki.

    Since the wiki has only one charset set by the admin, and the user
    interface files could have another charset, not all languages are
    available on every wiki - unless we move to Unicode for all
    languages translations. Even then, Python still can't recode some
    charsets.

    !!! Note: we use strict = 1 to choose only language that we can
    recode strictly from the language encodings to the wiki
    encoding. This preference could be left to the wiki admin instead.

    Return a dict containing a subset of MoinMoin languages ISO codes.
    """
    
    available = {}
    for lang in languages.keys():
        encoding = languages[lang][ENCODING].lower()
        if (encoding == config.charset or
            canRecode(encoding, config.charset, strict=1)):
            available[lang] = languages[lang]
        
    return available


def browserLanguages(request):
    """
    Return the accepted languages as set in the user browser.
    
    Parse the HTTP headers and extract the accepted languages,
    according to
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4

    Return a list of languages and base languages - as they are
    specified in the request, normalizing to lower case.
    """
    
    fallback = []
    
    accepted = request.http_accept_language

    if accepted:
        # Extract the languages names from the string
        accepted = accepted.split(',')

        accepted = map(lambda x: x.split(';')[0], accepted)

        # Add base language for each sub language. If the user specified
        # a sub language like "en-us", we will try to to provide it or
        # a least the base language "en" in this case.
        for lang in accepted:
            lang = lang.lower()
            fallback.append(lang)
            if '-' in lang:
                baselang = lang.split('-')[0]
                fallback.append(baselang)

    return fallback


def getDirection(lang):
    """Return the text direction for a language, either 'ltr' or 'rtl'."""
    return ('ltr', 'rtl')[languages[lang][DIRECTION]]


def getText(str, request, lang, formatted = True):
    """
    Return a translation of text in the user's language.
    """
    # TODO: Should move this into a language instance. request.lang should be a language instance.

    # load texts if needed
    global _text_cache
    if not _text_cache.has_key(lang):
        (texts, unformatted) = loadLanguage(request, lang)
        # XXX add error handling
        _text_cache[lang] = texts
        _unformatted_text_cache[lang] = unformatted

    # get the matching entry in the mapping table

    trans = str
    try:
        if formatted:
            trans = _text_cache[lang][str]
        else:
            trans = _unformatted_text_cache[lang][str]
    except KeyError:
        try:
            language = languages[lang][ENAME]
            dictpagename = "%sDict" % language
            if Page(request, dictpagename).exists():
                dicts = request.dicts
                if dicts.has_dict(dictpagename):
                    userdict = dicts.dict(dictpagename)
                    trans = userdict[str]
        except KeyError:
            pass
    return trans


########################################################################
# Encoding
########################################################################

def canRecode(input, output, strict=1):
    """
    Check if we can recode text from input to output.

    Return 1 if we can probably recode from one charset to
    another, or 0 if the charset are not known or compatible.

    arguments:
    input -- the input encoding codec name or alias
    output -- the output encoding codec name or alias
    strict -- Are you going to recode using errors='strict' or you can
    get with 'ignore', 'replace' or other error levels?
    """

    import codecs

    # First normalize case - our client could have funny ideas about case
    input = input.lower()
    output = output.lower()

    # Check for known encodings
    try:
        encoder = codecs.getencoder(output)
        decoder = codecs.getdecoder(input)          
    except LookupError:
        # Unknown encoding - forget about it!
        return 0
    
    # We assume that any charset that Python knows about, can be recoded
    # into any Unicode charset. Because codecs have many aliases, we
    # check the codec name itself
    if encoder.__name__.startswith('utf'):
        # This is a unicode encoding, so input could be anything.
        return 1

    # We know both encodings but we don't know if we can actually recode
    # any text from one to another. For example, we can recode from
    # iso-8859-8 to cp1255, because the first is a subset of the last,
    # but not the other way around.
    # We choose our answer according to the strict keyword argument
    if strict:
        # We are not sure, so NO
        return 0
    else:
        # Probably you can recode using 'replace' or 'ignore' or other
        # encodings error level and be happy with the results, so YES
        return 1

