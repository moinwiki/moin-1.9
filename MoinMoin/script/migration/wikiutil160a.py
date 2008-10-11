# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Utility Functions

    @copyright: 2000 - 2004 by Jürgen Hermann <jh@web.de>
                2007 by Reimar Bauer
    @license: GNU GPL, see COPYING for details.
"""

import cgi
import codecs
import os
import re
import time
import urllib

from MoinMoin import config
from MoinMoin.util import pysupport, lock

# Exceptions
class InvalidFileNameError(Exception):
    """ Called when we find an invalid file name """
    pass

# constants for page names
PARENT_PREFIX = "../"
PARENT_PREFIX_LEN = len(PARENT_PREFIX)
CHILD_PREFIX = "/"
CHILD_PREFIX_LEN = len(CHILD_PREFIX)

#############################################################################
### Getting data from user/Sending data to user
#############################################################################

def decodeWindowsPath(text):
    """ Decode Windows path names correctly. This is needed because many CGI
    servers follow the RFC recommendation and re-encode the path_info variable
    according to the file system semantics.

    @param text: the text to decode, string
    @rtype: unicode
    @return: decoded text
    """

    import locale
    cur_charset = locale.getdefaultlocale()[1]
    try:
        return unicode(text, 'utf-8')
    except UnicodeError:
        try:
            return unicode(text, cur_charset, 'replace')
        except LookupError:
            return unicode(text, 'iso-8859-1', 'replace')

def decodeUnknownInput(text):
    """ Decode unknown input, like text attachments

    First we try utf-8 because it has special format, and it will decode
    only utf-8 files. Then we try config.charset, then iso-8859-1 using
    'replace'. We will never raise an exception, but may return junk
    data.

    WARNING: Use this function only for data that you view, not for data
    that you save in the wiki.

    @param text: the text to decode, string
    @rtype: unicode
    @return: decoded text (maybe wrong)
    """
    # Shortcut for unicode input
    if isinstance(text, unicode):
        return text

    try:
        return unicode(text, 'utf-8')
    except UnicodeError:
        if config.charset not in ['utf-8', 'iso-8859-1']:
            try:
                return unicode(text, config.charset)
            except UnicodeError:
                pass
        return unicode(text, 'iso-8859-1', 'replace')


def decodeUserInput(s, charsets=[config.charset]):
    """
    Decodes input from the user.

    @param s: the string to unquote
    @param charsets: list of charsets to assume the string is in
    @rtype: unicode
    @return: the unquoted string as unicode
    """
    for charset in charsets:
        try:
            return s.decode(charset)
        except UnicodeError:
            pass
    raise UnicodeError('The string %r cannot be decoded.' % s)


# this is a thin wrapper around urllib (urllib only handles str, not unicode)
# with py <= 2.4.1, it would give incorrect results with unicode
# with py == 2.4.2, it crashes with unicode, if it contains non-ASCII chars
def url_quote(s, safe='/', want_unicode=False):
    """
    Wrapper around urllib.quote doing the encoding/decoding as usually wanted:

    @param s: the string to quote (can be str or unicode, if it is unicode,
              config.charset is used to encode it before calling urllib)
    @param safe: just passed through to urllib
    @param want_unicode: for the less usual case that you want to get back
                         unicode and not str, set this to True
                         Default is False.
    """
    if isinstance(s, unicode):
        s = s.encode(config.charset)
    elif not isinstance(s, str):
        s = str(s)
    s = urllib.quote(s, safe)
    if want_unicode:
        s = s.decode(config.charset) # ascii would also work
    return s

def url_quote_plus(s, safe='/', want_unicode=False):
    """
    Wrapper around urllib.quote_plus doing the encoding/decoding as usually wanted:

    @param s: the string to quote (can be str or unicode, if it is unicode,
              config.charset is used to encode it before calling urllib)
    @param safe: just passed through to urllib
    @param want_unicode: for the less usual case that you want to get back
                         unicode and not str, set this to True
                         Default is False.
    """
    if isinstance(s, unicode):
        s = s.encode(config.charset)
    elif not isinstance(s, str):
        s = str(s)
    s = urllib.quote_plus(s, safe)
    if want_unicode:
        s = s.decode(config.charset) # ascii would also work
    return s

def url_unquote(s, want_unicode=True):
    """
    Wrapper around urllib.unquote doing the encoding/decoding as usually wanted:

    @param s: the string to unquote (can be str or unicode, if it is unicode,
              config.charset is used to encode it before calling urllib)
    @param want_unicode: for the less usual case that you want to get back
                         str and not unicode, set this to False.
                         Default is True.
    """
    if isinstance(s, unicode):
        s = s.encode(config.charset) # ascii would also work
    s = urllib.unquote(s)
    if want_unicode:
        s = s.decode(config.charset)
    return s

def parseQueryString(qstr, want_unicode=True):
    """ Parse a querystring "key=value&..." into a dict.
    """
    is_unicode = isinstance(qstr, unicode)
    if is_unicode:
        qstr = qstr.encode(config.charset)
    values = {}
    for key, value in cgi.parse_qs(qstr).items():
        if len(value) < 2:
            v = ''.join(value)
            if want_unicode:
                try:
                    v = unicode(v, config.charset)
                except UnicodeDecodeError:
                    v = unicode(v, 'iso-8859-1', 'replace')
            values[key] = v
    return values

def makeQueryString(qstr=None, want_unicode=False, **kw):
    """ Make a querystring from arguments.

    kw arguments overide values in qstr.

    If a string is passed in, it's returned verbatim and
    keyword parameters are ignored.

    @param qstr: dict to format as query string, using either ascii or unicode
    @param kw: same as dict when using keywords, using ascii or unicode
    @rtype: string
    @return: query string ready to use in a url
    """
    if qstr is None:
        qstr = {}
    if isinstance(qstr, dict):
        qstr.update(kw)
        items = ['%s=%s' % (url_quote_plus(key, want_unicode=want_unicode), url_quote_plus(value, want_unicode=want_unicode)) for key, value in qstr.items()]
        qstr = '&'.join(items)
    return qstr


def quoteWikinameURL(pagename, charset=config.charset):
    """ Return a url encoding of filename in plain ascii

    Use urllib.quote to quote any character that is not always safe.

    @param pagename: the original pagename (unicode)
    @param charset: url text encoding, 'utf-8' recommended. Other charset
                    might not be able to encode the page name and raise
                    UnicodeError. (default config.charset ('utf-8')).
    @rtype: string
    @return: the quoted filename, all unsafe characters encoded
    """
    pagename = pagename.encode(charset)
    return urllib.quote(pagename)


def escape(s, quote=0):
    """ Escape possible html tags

    Replace special characters '&', '<' and '>' by SGML entities.
    (taken from cgi.escape so we don't have to include that, even if we
    don't use cgi at all)

    @param s: (unicode) string to escape
    @param quote: bool, should transform '\"' to '&quot;'
    @rtype: when called with a unicode object, return unicode object - otherwise return string object
    @return: escaped version of s
    """
    if not isinstance(s, (str, unicode)):
        s = str(s)

    # Must first replace &
    s = s.replace("&", "&amp;")

    # Then other...
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    if quote:
        s = s.replace('"', "&quot;")
    return s

def clean_comment(comment):
    """ Clean comment - replace CR, LF, TAB by whitespace, delete control chars
        TODO: move this to config, create on first call then return cached.
    """
    # we only have input fields with max 200 chars, but spammers send us more
    if len(comment) > 201:
        comment = u''
    remap_chars = {
        ord(u'\t'): u' ',
        ord(u'\r'): u' ',
        ord(u'\n'): u' ',
    }
    control_chars = u'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f' \
                    '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'
    for c in control_chars:
        remap_chars[c] = None
    comment = comment.translate(remap_chars)
    return comment

def make_breakable(text, maxlen):
    """ make a text breakable by inserting spaces into nonbreakable parts
    """
    text = text.split(" ")
    newtext = []
    for part in text:
        if len(part) > maxlen:
            while part:
                newtext.append(part[:maxlen])
                part = part[maxlen:]
        else:
            newtext.append(part)
    return " ".join(newtext)

########################################################################
### Storage
########################################################################

# Precompiled patterns for file name [un]quoting
UNSAFE = re.compile(r'[^a-zA-Z0-9_]+')
QUOTED = re.compile(r'\(([a-fA-F0-9]+)\)')


def quoteWikinameFS(wikiname, charset=config.charset):
    """ Return file system representation of a Unicode WikiName.

    Warning: will raise UnicodeError if wikiname can not be encoded using
    charset. The default value of config.charset, 'utf-8' can encode any
    character.

    @param wikiname: Unicode string possibly containing non-ascii characters
    @param charset: charset to encode string
    @rtype: string
    @return: quoted name, safe for any file system
    """
    filename = wikiname.encode(charset)

    quoted = []
    location = 0
    for needle in UNSAFE.finditer(filename):
        # append leading safe stuff
        quoted.append(filename[location:needle.start()])
        location = needle.end()
        # Quote and append unsafe stuff
        quoted.append('(')
        for character in needle.group():
            quoted.append('%02x' % ord(character))
        quoted.append(')')

    # append rest of string
    quoted.append(filename[location:])
    return ''.join(quoted)


def unquoteWikiname(filename, charsets=[config.charset]):
    """ Return Unicode WikiName from quoted file name.

    We raise an InvalidFileNameError if we find an invalid name, so the
    wiki could alarm the admin or suggest the user to rename a page.
    Invalid file names should never happen in normal use, but are rather
    cheap to find.

    This function should be used only to unquote file names, not page
    names we receive from the user. These are handled in request by
    urllib.unquote, decodePagename and normalizePagename.

    Todo: search clients of unquoteWikiname and check for exceptions.

    @param filename: string using charset and possibly quoted parts
    @param charsets: list of charsets used by string
    @rtype: Unicode String
    @return: WikiName
    """
    ### Temporary fix start ###
    # From some places we get called with Unicode strings
    if isinstance(filename, type(u'')):
        filename = filename.encode(config.charset)
    ### Temporary fix end ###

    parts = []
    start = 0
    for needle in QUOTED.finditer(filename):
        # append leading unquoted stuff
        parts.append(filename[start:needle.start()])
        start = needle.end()
        # Append quoted stuff
        group = needle.group(1)
        # Filter invalid filenames
        if (len(group) % 2 != 0):
            raise InvalidFileNameError(filename)
        try:
            for i in range(0, len(group), 2):
                byte = group[i:i+2]
                character = chr(int(byte, 16))
                parts.append(character)
        except ValueError:
            # byte not in hex, e.g 'xy'
            raise InvalidFileNameError(filename)

    # append rest of string
    if start == 0:
        wikiname = filename
    else:
        parts.append(filename[start:len(filename)])
        wikiname = ''.join(parts)

    # FIXME: This looks wrong, because at this stage "()" can be both errors
    # like open "(" without close ")", or unquoted valid characters in the file name.
    # Filter invalid filenames. Any left (xx) must be invalid
    #if '(' in wikiname or ')' in wikiname:
    #    raise InvalidFileNameError(filename)

    wikiname = decodeUserInput(wikiname, charsets)
    return wikiname

# time scaling
def timestamp2version(ts):
    """ Convert UNIX timestamp (may be float or int) to our version
        (long) int.
        We don't want to use floats, so we just scale by 1e6 to get
        an integer in usecs.
    """
    return long(ts*1000000L) # has to be long for py 2.2.x

def version2timestamp(v):
    """ Convert version number to UNIX timestamp (float).
        This must ONLY be used for display purposes.
    """
    return v / 1000000.0


# This is the list of meta attribute names to be treated as integers.
# IMPORTANT: do not use any meta attribute names with "-" (or any other chars
# invalid in python attribute names), use e.g. _ instead.
INTEGER_METAS = ['current', 'revision', # for page storage (moin 2.0)
                 'data_format_revision', # for data_dir format spec (use by mig scripts)
                ]

class MetaDict(dict):
    """ store meta informations as a dict.
    """
    def __init__(self, metafilename, cache_directory):
        """ create a MetaDict from metafilename """
        dict.__init__(self)
        self.metafilename = metafilename
        self.dirty = False
        lock_dir = os.path.join(cache_directory, '__metalock__')
        self.rlock = lock.ReadLock(lock_dir, 60.0)
        self.wlock = lock.WriteLock(lock_dir, 60.0)

        if not self.rlock.acquire(3.0):
            raise EnvironmentError("Could not lock in MetaDict")
        try:
            self._get_meta()
        finally:
            self.rlock.release()

    def _get_meta(self):
        """ get the meta dict from an arbitrary filename.
            does not keep state, does uncached, direct disk access.
            @param metafilename: the name of the file to read
            @return: dict with all values or {} if empty or error
        """

        try:
            metafile = codecs.open(self.metafilename, "r", "utf-8")
            meta = metafile.read() # this is much faster than the file's line-by-line iterator
            metafile.close()
        except IOError:
            meta = u''
        for line in meta.splitlines():
            key, value = line.split(':', 1)
            value = value.strip()
            if key in INTEGER_METAS:
                value = int(value)
            dict.__setitem__(self, key, value)

    def _put_meta(self):
        """ put the meta dict into an arbitrary filename.
            does not keep or modify state, does uncached, direct disk access.
            @param metafilename: the name of the file to write
            @param metadata: dict of the data to write to the file
        """
        meta = []
        for key, value in self.items():
            if key in INTEGER_METAS:
                value = str(value)
            meta.append("%s: %s" % (key, value))
        meta = '\r\n'.join(meta)

        metafile = codecs.open(self.metafilename, "w", "utf-8")
        metafile.write(meta)
        metafile.close()
        self.dirty = False

    def sync(self, mtime_usecs=None):
        """ No-Op except for that parameter """
        if not mtime_usecs is None:
            self.__setitem__('mtime', str(mtime_usecs))
        # otherwise no-op

    def __getitem__(self, key):
        """ We don't care for cache coherency here. """
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        """ Sets a dictionary entry. """
        if not self.wlock.acquire(5.0):
            raise EnvironmentError("Could not lock in MetaDict")
        try:
            self._get_meta() # refresh cache
            try:
                oldvalue = dict.__getitem__(self, key)
            except KeyError:
                oldvalue = None
            if value != oldvalue:
                dict.__setitem__(self, key, value)
                self._put_meta() # sync cache
        finally:
            self.wlock.release()


# Quoting of wiki names, file names, etc. (in the wiki markup) -----------------------------------

QUOTE_CHARS = u"'\""

def quoteName(name):
    """ put quotes around a given name """
    for quote_char in QUOTE_CHARS:
        if quote_char not in name:
            return u"%s%s%s" % (quote_char, name, quote_char)
    else:
        return name # XXX we need to be able to escape the quote char for worst case

def unquoteName(name):
    """ if there are quotes around the name, strip them """
    for quote_char in QUOTE_CHARS:
        if quote_char == name[0] == name[-1]:
            return name[1:-1]
    else:
        return name

#############################################################################
### InterWiki
#############################################################################
INTERWIKI_PAGE = "InterWikiMap"

def generate_file_list(request):
    """ generates a list of all files. for internal use. """

    # order is important here, the local intermap file takes
    # precedence over the shared one, and is thus read AFTER
    # the shared one
    intermap_files = request.cfg.shared_intermap
    if not isinstance(intermap_files, list):
        intermap_files = [intermap_files]
    else:
        intermap_files = intermap_files[:]
    intermap_files.append(os.path.join(request.cfg.data_dir, "intermap.txt"))
    request.cfg.shared_intermap_files = [filename for filename in intermap_files
                                         if filename and os.path.isfile(filename)]


def get_max_mtime(file_list, page):
    """ Returns the highest modification time of the files in file_list and the
    page page. """
    timestamps = [os.stat(filename).st_mtime for filename in file_list]
    if page.exists():
        # exists() is cached and thus cheaper than mtime_usecs()
        timestamps.append(version2timestamp(page.mtime_usecs()))
    return max(timestamps)


def load_wikimap(request):
    """ load interwiki map (once, and only on demand) """
    from MoinMoin.Page import Page

    now = int(time.time())
    if getattr(request.cfg, "shared_intermap_files", None) is None:
        generate_file_list(request)

    try:
        _interwiki_list = request.cfg.cache.interwiki_list
        old_mtime = request.cfg.cache.interwiki_mtime
        if request.cfg.cache.interwiki_ts + (1*60) < now: # 1 minutes caching time
            max_mtime = get_max_mtime(request.cfg.shared_intermap_files, Page(request, INTERWIKI_PAGE))
            if max_mtime > old_mtime:
                raise AttributeError # refresh cache
            else:
                request.cfg.cache.interwiki_ts = now
    except AttributeError:
        _interwiki_list = {}
        lines = []

        for filename in request.cfg.shared_intermap_files:
            f = open(filename, "r")
            lines.extend(f.readlines())
            f.close()

        # add the contents of the InterWikiMap page
        lines += Page(request, INTERWIKI_PAGE).get_raw_body().splitlines()

        for line in lines:
            if not line or line[0] == '#': continue
            try:
                line = "%s %s/InterWiki" % (line, request.getScriptname())
                wikitag, urlprefix, dummy = line.split(None, 2)
            except ValueError:
                pass
            else:
                _interwiki_list[wikitag] = urlprefix

        del lines

        # add own wiki as "Self" and by its configured name
        _interwiki_list['Self'] = request.getScriptname() + '/'
        if request.cfg.interwikiname:
            _interwiki_list[request.cfg.interwikiname] = request.getScriptname() + '/'

        # save for later
        request.cfg.cache.interwiki_list = _interwiki_list
        request.cfg.cache.interwiki_ts = now
        request.cfg.cache.interwiki_mtime = get_max_mtime(request.cfg.shared_intermap_files, Page(request, INTERWIKI_PAGE))

    return _interwiki_list

def split_wiki(wikiurl):
    """ Split a wiki url, e.g:

    'MoinMoin:FrontPage' -> "MoinMoin", "FrontPage", ""
    'FrontPage' -> "Self", "FrontPage", ""
    'MoinMoin:"Page with blanks" link title' -> "MoinMoin", "Page with blanks", "link title"

    can also be used for:

    'attachment:"filename with blanks.txt" other title' -> "attachment", "filename with blanks.txt", "other title"

    @param wikiurl: the url to split
    @rtype: tuple
    @return: (wikiname, pagename, linktext)
    """
    try:
        wikiname, rest = wikiurl.split(":", 1) # e.g. MoinMoin:FrontPage
    except ValueError:
        try:
            wikiname, rest = wikiurl.split("/", 1) # for what is this used?
        except ValueError:
            wikiname, rest = 'Self', wikiurl
    if rest:
        first_char = rest[0]
        if first_char in QUOTE_CHARS: # quoted pagename
            pagename_linktext = rest[1:].split(first_char, 1)
        else: # not quoted, split on whitespace
            pagename_linktext = rest.split(None, 1)
    else:
        pagename_linktext = "", ""
    if len(pagename_linktext) == 1:
        pagename, linktext = pagename_linktext[0], ""
    else:
        pagename, linktext = pagename_linktext
    linktext = linktext.strip()
    return wikiname, pagename, linktext

def resolve_wiki(request, wikiurl):
    """ Resolve an interwiki link.

    @param request: the request object
    @param wikiurl: the InterWiki:PageName link
    @rtype: tuple
    @return: (wikitag, wikiurl, wikitail, err)
    """
    _interwiki_list = load_wikimap(request)
    wikiname, pagename, linktext = split_wiki(wikiurl)
    if _interwiki_list.has_key(wikiname):
        return (wikiname, _interwiki_list[wikiname], pagename, False)
    else:
        return (wikiname, request.getScriptname(), "/InterWiki", True)

def join_wiki(wikiurl, wikitail):
    """
    Add a (url_quoted) page name to an interwiki url.

    Note: We can't know what kind of URL quoting a remote wiki expects.
          We just use a utf-8 encoded string with standard URL quoting.

    @param wikiurl: wiki url, maybe including a $PAGE placeholder
    @param wikitail: page name
    @rtype: string
    @return: generated URL of the page in the other wiki
    """
    wikitail = url_quote(wikitail)
    if '$PAGE' in wikiurl:
        return wikiurl.replace('$PAGE', wikitail)
    else:
        return wikiurl + wikitail


#############################################################################
### Page types (based on page names)
#############################################################################

def isSystemPage(request, pagename):
    """ Is this a system page? Uses AllSystemPagesGroup internally.

    @param request: the request object
    @param pagename: the page name
    @rtype: bool
    @return: true if page is a system page
    """
    return (request.dicts.has_member('SystemPagesGroup', pagename) or
        isTemplatePage(request, pagename))


def isTemplatePage(request, pagename):
    """ Is this a template page?

    @param pagename: the page name
    @rtype: bool
    @return: true if page is a template page
    """
    return request.cfg.cache.page_template_regex.search(pagename) is not None


def isGroupPage(request, pagename):
    """ Is this a name of group page?

    @param pagename: the page name
    @rtype: bool
    @return: true if page is a form page
    """
    return request.cfg.cache.page_group_regex.search(pagename) is not None


def filterCategoryPages(request, pagelist):
    """ Return category pages in pagelist

    WARNING: DO NOT USE THIS TO FILTER THE FULL PAGE LIST! Use
    getPageList with a filter function.

    If you pass a list with a single pagename, either that is returned
    or an empty list, thus you can use this function like a `isCategoryPage`
    one.

    @param pagelist: a list of pages
    @rtype: list
    @return: only the category pages of pagelist
    """
    func = request.cfg.cache.page_category_regex.search
    return filter(func, pagelist)


def getLocalizedPage(request, pagename): # was: getSysPage
    """ Get a system page according to user settings and available translations.

    We include some special treatment for the case that <pagename> is the
    currently rendered page, as this is the case for some pages used very
    often, like FrontPage, RecentChanges etc. - in that case we reuse the
    already existing page object instead creating a new one.

    @param request: the request object
    @param pagename: the name of the page
    @rtype: Page object
    @return: the page object of that system page, using a translated page,
             if it exists
    """
    from MoinMoin.Page import Page
    i18n_name = request.getText(pagename, formatted=False)
    pageobj = None
    if i18n_name != pagename:
        if request.page and i18n_name == request.page.page_name:
            # do not create new object for current page
            i18n_page = request.page
            if i18n_page.exists():
                pageobj = i18n_page
        else:
            i18n_page = Page(request, i18n_name)
            if i18n_page.exists():
                pageobj = i18n_page

    # if we failed getting a translated version of <pagename>,
    # we fall back to english
    if not pageobj:
        if request.page and pagename == request.page.page_name:
            # do not create new object for current page
            pageobj = request.page
        else:
            pageobj = Page(request, pagename)
    return pageobj


def getFrontPage(request):
    """ Convenience function to get localized front page

    @param request: current request
    @rtype: Page object
    @return localized page_front_page, if there is a translation
    """
    return getLocalizedPage(request, request.cfg.page_front_page)


def getHomePage(request, username=None):
    """
    Get a user's homepage, or return None for anon users and
    those who have not created a homepage.

    DEPRECATED - try to use getInterwikiHomePage (see below)

    @param request: the request object
    @param username: the user's name
    @rtype: Page
    @return: user's homepage object - or None
    """
    from MoinMoin.Page import Page
    # default to current user
    if username is None and request.user.valid:
        username = request.user.name

    # known user?
    if username:
        # Return home page
        page = Page(request, username)
        if page.exists():
            return page

    return None


def getInterwikiHomePage(request, username=None):
    """
    Get a user's homepage.

    cfg.user_homewiki influences behaviour of this:
    'Self' does mean we store user homepage in THIS wiki.
    When set to our own interwikiname, it behaves like with 'Self'.

    'SomeOtherWiki' means we store user homepages in another wiki.

    @param request: the request object
    @param username: the user's name
    @rtype: tuple (or None for anon users)
    @return: (wikiname, pagename)
    """
    # default to current user
    if username is None and request.user.valid:
        username = request.user.name
    if not username:
        return None # anon user

    homewiki = request.cfg.user_homewiki
    if homewiki == request.cfg.interwikiname:
        homewiki = 'Self'

    return homewiki, username


def AbsPageName(request, context, pagename):
    """
    Return the absolute pagename for a (possibly) relative pagename.

    @param context: name of the page where "pagename" appears on
    @param pagename: the (possibly relative) page name
    @rtype: string
    @return: the absolute page name
    """
    if pagename.startswith(PARENT_PREFIX):
        pagename = '/'.join(filter(None, context.split('/')[:-1] + [pagename[PARENT_PREFIX_LEN:]]))
    elif pagename.startswith(CHILD_PREFIX):
        pagename = context + '/' + pagename[CHILD_PREFIX_LEN:]
    return pagename

def pagelinkmarkup(pagename):
    """ return markup that can be used as link to page <pagename> """
    from MoinMoin.parser.text_moin_wiki import Parser
    if re.match(Parser.word_rule + "$", pagename):
        return pagename
    else:
        return u'["%s"]' % pagename # XXX use quoteName(pagename) later

#############################################################################
### mimetype support
#############################################################################
import mimetypes

MIMETYPES_MORE = {
 # OpenOffice 2.x & other open document stuff
 '.odt': 'application/vnd.oasis.opendocument.text',
 '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
 '.odp': 'application/vnd.oasis.opendocument.presentation',
 '.odg': 'application/vnd.oasis.opendocument.graphics',
 '.odc': 'application/vnd.oasis.opendocument.chart',
 '.odf': 'application/vnd.oasis.opendocument.formula',
 '.odb': 'application/vnd.oasis.opendocument.database',
 '.odi': 'application/vnd.oasis.opendocument.image',
 '.odm': 'application/vnd.oasis.opendocument.text-master',
 '.ott': 'application/vnd.oasis.opendocument.text-template',
 '.ots': 'application/vnd.oasis.opendocument.spreadsheet-template',
 '.otp': 'application/vnd.oasis.opendocument.presentation-template',
 '.otg': 'application/vnd.oasis.opendocument.graphics-template',
}
[mimetypes.add_type(mimetype, ext, True) for ext, mimetype in MIMETYPES_MORE.items()]

MIMETYPES_sanitize_mapping = {
    # this stuff is text, but got application/* for unknown reasons
    ('application', 'docbook+xml'): ('text', 'docbook'),
    ('application', 'x-latex'): ('text', 'latex'),
    ('application', 'x-tex'): ('text', 'tex'),
    ('application', 'javascript'): ('text', 'javascript'),
}

MIMETYPES_spoil_mapping = {} # inverse mapping of above
for key, value in MIMETYPES_sanitize_mapping.items():
    MIMETYPES_spoil_mapping[value] = key


class MimeType(object):
    """ represents a mimetype like text/plain """

    def __init__(self, mimestr=None, filename=None):
        self.major = self.minor = None # sanitized mime type and subtype
        self.params = {} # parameters like "charset" or others
        self.charset = None # this stays None until we know for sure!
        self.raw_mimestr = mimestr

        if mimestr:
            self.parse_mimetype(mimestr)
        elif filename:
            self.parse_filename(filename)

    def parse_filename(self, filename):
        mtype, encoding = mimetypes.guess_type(filename)
        if mtype is None:
            mtype = 'application/octet-stream'
        self.parse_mimetype(mtype)

    def parse_mimetype(self, mimestr):
        """ take a string like used in content-type and parse it into components,
            alternatively it also can process some abbreviated string like "wiki"
        """
        parameters = mimestr.split(";")
        parameters = [p.strip() for p in parameters]
        mimetype, parameters = parameters[0], parameters[1:]
        mimetype = mimetype.split('/')
        if len(mimetype) >= 2:
            major, minor = mimetype[:2] # we just ignore more than 2 parts
        else:
            major, minor = self.parse_format(mimetype[0])
        self.major = major.lower()
        self.minor = minor.lower()
        for param in parameters:
            key, value = param.split('=')
            if value[0] == '"' and value[-1] == '"': # remove quotes
                value = value[1:-1]
            self.params[key.lower()] = value
        if self.params.has_key('charset'):
            self.charset = self.params['charset'].lower()
        self.sanitize()

    def parse_format(self, format):
        """ maps from what we currently use on-page in a #format xxx processing
            instruction to a sanitized mimetype major, minor tuple.
            can also be user later for easier entry by the user, so he can just
            type "wiki" instead of "text/moin-wiki".
        """
        format = format.lower()
        if format in ('plain', 'csv', 'rst', 'docbook', 'latex', 'tex', 'html', 'css',
                      'xml', 'python', 'perl', 'php', 'ruby', 'javascript',
                      'cplusplus', 'java', 'pascal', 'diff', 'gettext', 'xslt', ):
            mimetype = 'text', format
        else:
            mapping = {
                'wiki': ('text', 'moin-wiki'),
                'irc': ('text', 'irssi'),
            }
            try:
                mimetype = mapping[format]
            except KeyError:
                mimetype = 'text', 'x-%s' % format
        return mimetype

    def sanitize(self):
        """ convert to some representation that makes sense - this is not necessarily
            conformant to /etc/mime.types or IANA listing, but if something is
            readable text, we will return some text/* mimetype, not application/*,
            because we need text/plain as fallback and not application/octet-stream.
        """
        self.major, self.minor = MIMETYPES_sanitize_mapping.get((self.major, self.minor), (self.major, self.minor))

    def spoil(self):
        """ this returns something conformant to /etc/mime.type or IANA as a string,
            kind of inverse operation of sanitize(), but doesn't change self
        """
        major, minor = MIMETYPES_spoil_mapping.get((self.major, self.minor), (self.major, self.minor))
        return self.content_type(major, minor)

    def content_type(self, major=None, minor=None, charset=None, params=None):
        """ return a string suitable for Content-Type header
        """
        major = major or self.major
        minor = minor or self.minor
        params = params or self.params or {}
        if major == 'text':
            charset = charset or self.charset or params.get('charset', config.charset)
            params['charset'] = charset
        mimestr = "%s/%s" % (major, minor)
        params = ['%s="%s"' % (key.lower(), value) for key, value in params.items()]
        params.insert(0, mimestr)
        return "; ".join(params)

    def mime_type(self):
        """ return a string major/minor only, no params """
        return "%s/%s" % (self.major, self.minor)

    def module_name(self):
        """ convert this mimetype to a string useable as python module name,
            we yield the exact module name first and then proceed to shorter
            module names (useful for falling back to them, if the more special
            module is not found) - e.g. first "text_python", next "text".
            Finally, we yield "application_octet_stream" as the most general
            mimetype we have.
            Hint: the fallback handler module for text/* should be implemented
                  in module "text" (not "text_plain")
        """
        mimetype = self.mime_type()
        modname = mimetype.replace("/", "_").replace("-", "_").replace(".", "_")
        fragments = modname.split('_')
        for length in range(len(fragments), 1, -1):
            yield "_".join(fragments[:length])
        yield self.raw_mimestr
        yield fragments[0]
        yield "application_octet_stream"


#############################################################################
### Plugins
#############################################################################

class PluginError(Exception):
    """ Base class for plugin errors """

class PluginMissingError(PluginError):
    """ Raised when a plugin is not found """

class PluginAttributeError(PluginError):
    """ Raised when plugin does not contain an attribtue """


def importPlugin(cfg, kind, name, function="execute"):
    """ Import wiki or builtin plugin

    Returns function from a plugin module name. If name can not be
    imported, raise PluginMissingError. If function is missing, raise
    PluginAttributeError.

    kind may be one of 'action', 'formatter', 'macro', 'parser' or any other
    directory that exist in MoinMoin or data/plugin.

    Wiki plugins will always override builtin plugins. If you want
    specific plugin, use either importWikiPlugin or importBuiltinPlugin
    directly.

    @param cfg: wiki config instance
    @param kind: what kind of module we want to import
    @param name: the name of the module
    @param function: the function name
    @rtype: any object
    @return: "function" of module "name" of kind "kind", or None
    """
    try:
        return importWikiPlugin(cfg, kind, name, function)
    except PluginMissingError:
        return importBuiltinPlugin(kind, name, function)


def importWikiPlugin(cfg, kind, name, function="execute"):
    """ Import plugin from the wiki data directory

    See importPlugin docstring.
    """
    if not name in wikiPlugins(kind, cfg):
        raise PluginMissingError
    moduleName = '%s.plugin.%s.%s' % (cfg.siteid, kind, name)
    return importNameFromPlugin(moduleName, function)


def importBuiltinPlugin(kind, name, function="execute"):
    """ Import builtin plugin from MoinMoin package

    See importPlugin docstring.
    """
    if not name in builtinPlugins(kind):
        raise PluginMissingError
    moduleName = 'MoinMoin.%s.%s' % (kind, name)
    return importNameFromPlugin(moduleName, function)


def importNameFromPlugin(moduleName, name):
    """ Return name from plugin module

    Raise PluginAttributeError if name does not exists.
    """
    module = __import__(moduleName, globals(), {}, [name])
    try:
        return getattr(module, name)
    except AttributeError:
        raise PluginAttributeError


def builtinPlugins(kind):
    """ Gets a list of modules in MoinMoin.'kind'

    @param kind: what kind of modules we look for
    @rtype: list
    @return: module names
    """
    modulename = "MoinMoin." + kind
    return pysupport.importName(modulename, "modules")


def wikiPlugins(kind, cfg):
    """ Gets a list of modules in data/plugin/'kind'

    Require valid plugin directory. e.g missing 'parser' directory or
    missing '__init__.py' file will raise errors.

    @param kind: what kind of modules we look for
    @rtype: list
    @return: module names
    """
    # Wiki plugins are located in wikiconfig.plugin module
    modulename = '%s.plugin.%s' % (cfg.siteid, kind)
    return pysupport.importName(modulename, "modules")


def getPlugins(kind, cfg):
    """ Gets a list of plugin names of kind

    @param kind: what kind of modules we look for
    @rtype: list
    @return: module names
    """
    # Copy names from builtin plugins - so we dont destroy the value
    all_plugins = builtinPlugins(kind)[:]

    # Add extension plugins without duplicates
    for plugin in wikiPlugins(kind, cfg):
        if plugin not in all_plugins:
            all_plugins.append(plugin)

    return all_plugins


def searchAndImportPlugin(cfg, type, name, what=None):
    type2classname = {"parser": "Parser",
                      "formatter": "Formatter",
    }
    if what is None:
        what = type2classname[type]
    mt = MimeType(name)
    plugin = None
    for module_name in mt.module_name():
        try:
            plugin = importPlugin(cfg, type, module_name, what)
            break
        except PluginMissingError:
            pass
    else:
        raise PluginMissingError("Plugin not found!")
    return plugin


#############################################################################
### Parsers
#############################################################################

def getParserForExtension(cfg, extension):
    """
    Returns the Parser class of the parser fit to handle a file
    with the given extension. The extension should be in the same
    format as os.path.splitext returns it (i.e. with the dot).
    Returns None if no parser willing to handle is found.
    The dict of extensions is cached in the config object.

    @param cfg: the Config instance for the wiki in question
    @param extension: the filename extension including the dot
    @rtype: class, None
    @returns: the parser class or None
    """
    if not hasattr(cfg.cache, 'EXT_TO_PARSER'):
        etp, etd = {}, None
        for pname in getPlugins('parser', cfg):
            try:
                Parser = importPlugin(cfg, 'parser', pname, 'Parser')
            except PluginMissingError:
                continue
            if hasattr(Parser, 'extensions'):
                exts = Parser.extensions
                if isinstance(exts, list):
                    for ext in Parser.extensions:
                        etp[ext] = Parser
                elif str(exts) == '*':
                    etd = Parser
        cfg.cache.EXT_TO_PARSER = etp
        cfg.cache.EXT_TO_PARSER_DEFAULT = etd

    return cfg.cache.EXT_TO_PARSER.get(extension, cfg.cache.EXT_TO_PARSER_DEFAULT)


#############################################################################
### Parameter parsing
#############################################################################

def parseAttributes(request, attrstring, endtoken=None, extension=None):
    """
    Parse a list of attributes and return a dict plus a possible
    error message.
    If extension is passed, it has to be a callable that returns
    a tuple (found_flag, msg). found_flag is whether it did find and process
    something, msg is '' when all was OK or any other string to return an error
    message.

    @param request: the request object
    @param attrstring: string containing the attributes to be parsed
    @param endtoken: token terminating parsing
    @param extension: extension function -
                      gets called with the current token, the parser and the dict
    @rtype: dict, msg
    @return: a dict plus a possible error message
    """
    import shlex, StringIO

    _ = request.getText

    parser = shlex.shlex(StringIO.StringIO(attrstring))
    parser.commenters = ''
    msg = None
    attrs = {}

    while not msg:
        try:
            key = parser.get_token()
        except ValueError, err:
            msg = str(err)
            break
        if not key: break
        if endtoken and key == endtoken: break

        # call extension function with the current token, the parser, and the dict
        if extension:
            found_flag, msg = extension(key, parser, attrs)
            #request.log("%r = extension(%r, parser, %r)" % (msg, key, attrs))
            if found_flag:
                continue
            elif msg:
                break
            #else (we found nothing, but also didn't have an error msg) we just continue below:

        try:
            eq = parser.get_token()
        except ValueError, err:
            msg = str(err)
            break
        if eq != "=":
            msg = _('Expected "=" to follow "%(token)s"') % {'token': key}
            break

        try:
            val = parser.get_token()
        except ValueError, err:
            msg = str(err)
            break
        if not val:
            msg = _('Expected a value for key "%(token)s"') % {'token': key}
            break

        key = escape(key) # make sure nobody cheats

        # safely escape and quote value
        if val[0] in ["'", '"']:
            val = escape(val)
        else:
            val = '"%s"' % escape(val, 1)

        attrs[key.lower()] = val

    return attrs, msg or ''


class ParameterParser:
    """ MoinMoin macro parameter parser

        Parses a given parameter string, separates the individual parameters
        and detects their type.

        Possible parameter types are:

        Name      | short  | example
        ----------------------------
         Integer  | i      | -374
         Float    | f      | 234.234 23.345E-23
         String   | s      | 'Stri\'ng'
         Boolean  | b      | 0 1 True false
         Name     |        | case_sensitive | converted to string

        So say you want to parse three things, name, age and if the
        person is male or not:

        The pattern will be: %(name)s%(age)i%(male)b

        As a result, the returned dict will put the first value into
        male, second into age etc. If some argument is missing, it will
        get None as its value. This also means that all the identifiers
        in the pattern will exist in the dict, they will just have the
        value None if they were not specified by the caller.

        So if we call it with the parameters as follows:
            ("John Smith", 18)
        this will result in the following dict:
            {"name": "John Smith", "age": 18, "male": None}

        Another way of calling would be:
            ("John Smith", male=True)
        this will result in the following dict:
            {"name": "John Smith", "age": None, "male": True}

        @copyright: 2004 by Florian Festi,
                    2006 by Mikko Virkkilä
        @license: GNU GPL, see COPYING for details.
    """

    def __init__(self, pattern):
        #parameter_re = "([^\"',]*(\"[^\"]*\"|'[^']*')?[^\"',]*)[,)]"
        name = "(?P<%s>[a-zA-Z_][a-zA-Z0-9_]*)"
        int_re = r"(?P<int>-?\d+)"
        bool_re = r"(?P<bool>(([10])|([Tt]rue)|([Ff]alse)))"
        float_re = r"(?P<float>-?\d+\.\d+([eE][+-]?\d+)?)"
        string_re = (r"(?P<string>('([^']|(\'))*?')|" +
                                r'("([^"]|(\"))*?"))')
        name_re = name % "name"
        name_param_re = name % "name_param"

        param_re = r"\s*(\s*%s\s*=\s*)?(%s|%s|%s|%s|%s)\s*(,|$)" % (
                   name_re, float_re, int_re, bool_re, string_re, name_param_re)
        self.param_re = re.compile(param_re, re.U)
        self._parse_pattern(pattern)

    def _parse_pattern(self, pattern):
        param_re = r"(%(?P<name>\(.*?\))?(?P<type>[ibfs]{1,3}))|\|"
        i = 0
        # TODO: Optionals aren't checked.
        self.optional = []
        named = False
        self.param_list = []
        self.param_dict = {}

        for match in re.finditer(param_re, pattern):
            if match.group() == "|":
                self.optional.append(i)
                continue
            self.param_list.append(match.group('type'))
            if match.group('name'):
                named = True
                self.param_dict[match.group('name')[1:-1]] = i
            elif named:
                raise ValueError, "Named parameter expected"
            i += 1

    def __str__(self):
        return "%s, %s, optional:%s" % (self.param_list, self.param_dict,
                                        self.optional)

    def parse_parameters(self, input):
        """
        (4, 2)
        """
        #Default list to "None"s
        parameter_list = [None] * len(self.param_list)
        parameter_dict = {}
        check_list = [0] * len(self.param_list)

        i = 0
        start = 0
        named = False
        while start < len(input):
            match = re.match(self.param_re, input[start:])
            if not match:
                raise ValueError, "Misformatted value"
            start += match.end()
            value = None
            if match.group("int"):
                value = int(match.group("int"))
                type = 'i'
            elif match.group("bool"):
                value = (match.group("bool") == "1") or (match.group("bool") == "True") or (match.group("bool") == "true")
                type = 'b'
            elif match.group("float"):
                value = float(match.group("float"))
                type = 'f'
            elif match.group("string"):
                value = match.group("string")[1:-1]
                type = 's'
            elif match.group("name_param"):
                value = match.group("name_param")
                type = 'n'
            else:
                value = None

            parameter_list.append(value)
            if match.group("name"):
                if not self.param_dict.has_key(match.group("name")):
                    raise ValueError, "Unknown parameter name '%s'" % match.group("name")
                nr = self.param_dict[match.group("name")]
                if check_list[nr]:
                    #raise ValueError, "Parameter specified twice"
                    #TODO: Something saner that raising an exception. This is pretty good, since it ignores it.
                    pass
                else:
                    check_list[nr] = 1
                parameter_dict[match.group("name")] = value
                parameter_list[nr] = value
                named = True
            elif named:
                raise ValueError, "Only named parameters allowed"
            else:
                nr = i
                parameter_list[nr] = value

            #Let's populate and map our dictionary to what's been found
            for name in self.param_dict.keys():
                tmp = self.param_dict[name]
                parameter_dict[name]=parameter_list[tmp]

            i += 1

        return parameter_list, parameter_dict


""" never used:
    def _check_type(value, type, format):
        if type == 'n' and 's' in format: # n as s
            return value

        if type in format:
            return value # x -> x

        if type == 'i':
            if 'f' in format:
                return float(value) # i -> f
            elif 'b' in format:
                return value # i -> b
        elif type == 'f':
            if 'b' in format:
                return value  # f -> b
        elif type == 's':
            if 'b' in format:
                return value.lower() != 'false' # s-> b

        if 's' in format: # * -> s
            return str(value)
        else:
            pass # XXX error

def main():
    pattern = "%i%sf%s%ifs%(a)s|%(b)s"
    param = ' 4,"DI\'NG", b=retry, a="DING"'

    #p_list, p_dict = parse_parameters(param)

    print 'Pattern :', pattern
    print 'Param :', param

    P = ParameterParser(pattern)
    print P
    print P.parse_parameters(param)


if __name__=="__main__":
    main()
"""

#############################################################################
### Misc
#############################################################################
def taintfilename(basename):
    """
    Make a filename that is supposed to be a plain name secure, i.e.
    remove any possible path components that compromise our system.

    @param basename: (possibly unsafe) filename
    @rtype: string
    @return: (safer) filename
    """
    for x in (os.pardir, ':', '/', '\\', '<', '>'):
        basename = basename.replace(x, '_')

    return basename


def mapURL(request, url):
    """
    Map URLs according to 'cfg.url_mappings'.

    @param url: a URL
    @rtype: string
    @return: mapped URL
    """
    # check whether we have to map URLs
    if request.cfg.url_mappings:
        # check URL for the configured prefixes
        for prefix in request.cfg.url_mappings.keys():
            if url.startswith(prefix):
                # substitute prefix with replacement value
                return request.cfg.url_mappings[prefix] + url[len(prefix):]

    # return unchanged url
    return url


def getUnicodeIndexGroup(name):
    """
    Return a group letter for `name`, which must be a unicode string.
    Currently supported: Hangul Syllables (U+AC00 - U+D7AF)

    @param name: a string
    @rtype: string
    @return: group letter or None
    """
    c = name[0]
    if u'\uAC00' <= c <= u'\uD7AF': # Hangul Syllables
        return unichr(0xac00 + (int(ord(c) - 0xac00) / 588) * 588)
    else:
        return c.upper() # we put lower and upper case words into the same index group


def isStrictWikiname(name, word_re=re.compile(ur"^(?:[%(u)s][%(l)s]+){2,}$" % {'u': config.chars_upper, 'l': config.chars_lower})):
    """
    Check whether this is NOT an extended name.

    @param name: the wikiname in question
    @rtype: bool
    @return: true if name matches the word_re
    """
    return word_re.match(name)


def isPicture(url):
    """
    Is this a picture's url?

    @param url: the url in question
    @rtype: bool
    @return: true if url points to a picture
    """
    extpos = url.rfind(".")
    return extpos > 0 and url[extpos:].lower() in ['.gif', '.jpg', '.jpeg', '.png', '.bmp', '.ico', ]


def link_tag(request, params, text=None, formatter=None, on=None, **kw):
    """ Create a link.

    TODO: cleanup css_class

    @param request: the request object
    @param params: parameter string appended to the URL after the scriptname/
    @param text: text / inner part of the <a>...</a> link - does NOT get
                 escaped, so you can give HTML here and it will be used verbatim
    @param formatter: the formatter object to use
    @param on: opening/closing tag only
    @keyword attrs: additional attrs (HTMLified string) (removed in 1.5.3)
    @rtype: string
    @return: formatted link tag
    """
    if formatter is None:
        formatter = request.html_formatter
    if kw.has_key('css_class'):
        css_class = kw['css_class']
        del kw['css_class'] # one time is enough
    else:
        css_class = None
    id = kw.get('id', None)
    name = kw.get('name', None)
    if text is None:
        text = params # default
    if formatter:
        url = "%s/%s" % (request.getScriptname(), params)
        # formatter.url will escape the url part
        if on is not None:
            tag = formatter.url(on, url, css_class, **kw)
        else:
            tag = (formatter.url(1, url, css_class, **kw) +
                formatter.rawHTML(text) +
                formatter.url(0))
    else: # this shouldn't be used any more:
        if on is not None and not on:
            tag = '</a>'
        else:
            attrs = ''
            if css_class:
                attrs += ' class="%s"' % css_class
            if id:
                attrs += ' id="%s"' % id
            if name:
                attrs += ' name="%s"' % name
            tag = '<a%s href="%s/%s">' % (attrs, request.getScriptname(), params)
            if not on:
                tag = "%s%s</a>" % (tag, text)
        request.log("Warning: wikiutil.link_tag called without formatter and without request.html_formatter. tag=%r" % (tag, ))
    return tag

def containsConflictMarker(text):
    """ Returns true if there is a conflict marker in the text. """
    return "/!\\ '''Edit conflict" in text

def pagediff(request, pagename1, rev1, pagename2, rev2, **kw):
    """
    Calculate the "diff" between two page contents.

    @param pagename1: name of first page
    @param rev1: revision of first page
    @param pagename2: name of second page
    @param rev2: revision of second page
    @keyword ignorews: if 1: ignore pure-whitespace changes.
    @rtype: list
    @return: lines of diff output
    """
    from MoinMoin.Page import Page
    from MoinMoin.util import diff_text
    lines1 = Page(request, pagename1, rev=rev1).getlines()
    lines2 = Page(request, pagename2, rev=rev2).getlines()

    lines = diff_text.diff(lines1, lines2, **kw)
    return lines


########################################################################
### Tickets - used by RenamePage and DeletePage
########################################################################

def createTicket(request, tm=None):
    """Create a ticket using a site-specific secret (the config)"""
    from MoinMoin.support.python_compatibility import hash_new
    ticket = tm or "%010x" % time.time()
    digest = hash_new('sha1', ticket)

    varnames = ['data_dir', 'data_underlay_dir', 'language_default',
                'mail_smarthost', 'mail_from', 'page_front_page',
                'theme_default', 'sitename', 'logo_string',
                'interwikiname', 'user_homewiki', 'acl_rights_before', ]
    for varname in varnames:
        var = getattr(request.cfg, varname, None)
        if isinstance(var, (str, unicode)):
            digest.update(repr(var))

    return "%s.%s" % (ticket, digest.hexdigest())


def checkTicket(request, ticket):
    """Check validity of a previously created ticket"""
    try:
        timestamp_str = ticket.split('.')[0]
        timestamp = int(timestamp_str, 16)
    except ValueError:
        # invalid or empty ticket
        return False
    now = time.time()
    if timestamp < now - 10 * 3600:
        # we don't accept tickets older than 10h
        return False
    ourticket = createTicket(request, timestamp_str)
    return ticket == ourticket


def renderText(request, Parser, text, line_anchors=False):
    """executes raw wiki markup with all page elements"""
    import StringIO
    out = StringIO.StringIO()
    request.redirect(out)
    wikiizer = Parser(text, request)
    wikiizer.format(request.formatter, inhibit_p=True)
    result = out.getvalue()
    request.redirect()
    del out
    return result


def getProcessingInstructions(text):
    """creates dict of processing instructions from raw wiki markup"""
    kw = {}
    for line in text.split('\n'):
        if line.startswith('#'):
            for pi in ("format", "refresh", "redirect", "deprecated", "pragma", "form", "acl", "language"):
                if line[1:].lower().startswith(pi):
                    kw[pi] = line[len(pi)+1:].strip()
                    break
    return kw


def getParser(request, text):
    """gets the parser from raw wiki murkup"""
    # check for XML content
    if text and text[:5] == '<?xml':
        pi_format = "xslt"
    else:
        # check processing instructions
        pi = getProcessingInstructions(text)
        pi_format = pi.get("format", request.cfg.default_markup or "wiki").lower()

    Parser = searchAndImportPlugin(request.cfg, "parser", pi_format)
    return Parser

