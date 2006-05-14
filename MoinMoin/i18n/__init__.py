# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Internationalization

    This subpackage controls the access to the language modules contained in
    it. Each language is in a module with a dictionary storing the original
    texts as keys and their translation in the values. Other supporting modules
    start with an underscore.

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
    
    @copyright: 2001-2004 by Jürgen Hermann <jh@web.de>,
                2005-2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
debug = 0

import os
try:
    import cPickle as pickle
except ImportError:
    import pickle

# Set pickle protocol, see http://docs.python.org/lib/node64.html
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL

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

def filename(lang):
    """
    Return the filename for lang

    This is not always the same as the language name. This function hides
    the naming details from the clients.
    """
    filename = lang.replace('-', '_')
    filename = filename.lower()
    return filename

def formatMarkup(request, text, currentStack=[]):
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

    from MoinMoin.parser.wiki import Parser
    from MoinMoin.formatter.text_html import Formatter
    import StringIO

    origtext = text
    out = StringIO.StringIO()
    request.redirect(out)
    parser = Parser(text, request, line_anchors=False)
    formatter = Formatter(request, terse=True)
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
    # farm notice: for persistent servers, only the first wiki requesting some language
    # gets its cache updated - a bit strange and redundant, but no problem.
    cache = caching.CacheEntry(request, arena='i18n', key=lang)
    langfilename = os.path.join(os.path.dirname(__file__), '%s.py' % filename(lang))
    needsupdate = cache.needsUpdate(langfilename)
    if debug: request.log("i18n: langfilename %s needsupdate %d" % (langfilename, needsupdate))
    if not needsupdate:
        try:
            (uc_texts, uc_unformatted) = pickle.loads(cache.content())
        except (IOError, ValueError, pickle.UnpicklingError): # bad pickle data, no pickle
            if debug: request.log("i18n: pickle %s load failed" % lang)
            needsupdate = 1

    if needsupdate:    
        from MoinMoin.util import pysupport
        lang_module = "MoinMoin.i18n.%s" % filename(lang)
        try:
            # Language module without text dict will raise AttributeError
            texts = pysupport.importName(lang_module, "text")
        except ImportError:
            if debug: request.log("i18n: import of module %s failed." % lang_module)
            return None, None
        meta = pysupport.importName(lang_module, "meta") 
        encoding = meta['encoding']

        # convert to unicode
        if debug: request.log("i18n: processing unformatted texts of lang %s" % lang)
        uc_unformatted = {}
        for key, text in texts.items():
            ukey = key.decode(encoding)
            utext = text.decode(encoding)
            uc_unformatted[ukey] = utext

        if meta.get('wikimarkup', False):
            if debug: request.log("i18n: processing formatted texts of lang %s" % lang)
            # use the wiki parser now to replace some wiki markup with html
            uc_texts = {}
            for key, text in uc_unformatted.items():
                try:
                    uc_texts[key] = formatMarkup(request, text)
                except: # infinite recursion or crash
                    if debug:
                        request.log("i18n: crashes in language %s on string: %s" % (lang, text))
                    uc_texts[key] = "%s*" % text
        else:
            uc_texts = uc_unformatted
        if debug: request.log("i18n: dumping lang %s" % lang)
        cache.update(pickle.dumps((uc_texts, uc_unformatted), PICKLE_PROTOCOL))

    return uc_texts, uc_unformatted

def requestLanguage(request):
    """ 
    Return the user interface language for this request.
    
    The user interface language is taken from the user preferences for
    registered users, or request environment, or the default language of
    the wiki, or English.

    This should be called once per request, then you should get the value from
    request object lang attribute.
    
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
    if not request.cfg.language_ignore_browser:
        for lang in browserLanguages(request):
            if lang in available:
                if request.http_accept_language:
                    request.setHttpHeader('Vary: Accept-Language')
                return lang
    
    # Or return the wiki default language...
    if request.cfg.language_default in available:
        lang = request.cfg.language_default
    # If everything else fails, read the manual... or return 'en'
    else:
        lang = 'en'
    return lang

def wikiLanguages():
    """
    Return the available user languages in this wiki.
    As we do everything in unicode (or utf-8) now, everything is available.
    """
    return languages

def browserLanguages(request):
    """
    Return the accepted languages as set in the user browser.
    
    Parse the HTTP headers and extract the accepted languages, according to:
    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.4

    Return a list of languages and base languages - as they are specified in
    the request, normalizing to lower case.
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
    """ Return the text direction for a language, either 'ltr' or 'rtl'. """
    return ('ltr', 'rtl')[languages[lang][DIRECTION]]

def getText(str, request, lang, formatted=True):
    """ Return a translation of text in the user's language. """
    # TODO: Should move this into a language instance. request.lang should be a language instance.

    # load texts if needed
    global _text_cache
    if not lang in _text_cache:
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
            # do not simply return trans with str, but recursively call
            # to get english translation, maybe formatted
            if lang != 'en':
                trans = getText(str, request, 'en', formatted)
    return trans

