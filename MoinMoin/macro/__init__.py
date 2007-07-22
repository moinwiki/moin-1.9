# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Macro Implementation

    These macros are used by the wiki parser module to implement complex
    and/or dynamic page content.

    The canonical interface to plugin macros is their execute() function,
    which gets passed an instance of the Macro class. Such an instance
    has the four members parser, formatter, form and request.

    Using "form" directly is deprecated and should be replaced by "request.form".

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006-2007 MoinMoin:ThomasWaldmann,
                2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport
modules = pysupport.getPackageModules(__file__)

import re, time, os
from MoinMoin import action, config, util
from MoinMoin import wikiutil, i18n
from MoinMoin.Page import Page

names = ["TitleSearch", "WordIndex", "TitleIndex",
         "GoTo", "InterWiki", "PageCount",
         # Macros with arguments
         "Icon", "PageList", "Date", "DateTime", "Anchor", "MailTo", "GetVal",
         "TemplateList",
]

#############################################################################
### Helpers
#############################################################################

def getNames(cfg):
    if not hasattr(cfg.cache, 'macro_names'):
        lnames = names[:]
        lnames.extend(i18n.wikiLanguages().keys())
        lnames.extend(wikiutil.getPlugins('macro', cfg))
        cfg.cache.macro_names = lnames # remember it
    return cfg.cache.macro_names


#############################################################################
### Macros - Handlers for [[macroname]] markup
#############################################################################

class Macro:
    """ Macro handler

    There are three kinds of macros:
     * Builtin Macros - implemented in this file and named macro_[name]
     * Language Pseudo Macros - any lang the wiki knows can be use as
       macro and is implemented here by _m_lang()
     * External macros - implemented in either MoinMoin.macro package, or
       in the specific wiki instance in the plugin/macro directory
    """
    defaultDependency = ["time"]

    Dependencies = {
        "TitleSearch": ["namespace"],
        "Goto": [],
        "WordIndex": ["namespace"],
        "TitleIndex": ["namespace"],
        "InterWiki": ["pages"],  # if interwikimap is editable
        "PageCount": ["namespace"],
        "Icon": ["user"], # users have different themes and user prefs
        "PageList": ["namespace"],
        "Date": ["time"],
        "DateTime": ["time"],
        "Anchor": [],
        "Mailto": ["user"],
        "GetVal": ["pages"],
        "TemplateList": ["namespace"],
        }

    # we need the lang macros to execute when html is generated,
    # to have correct dir and lang html attributes
    for lang in i18n.wikiLanguages():
        Dependencies[lang] = []


    def __init__(self, parser):
        self.parser = parser
        self.form = self.parser.form
        self.request = self.parser.request
        self.formatter = self.request.formatter
        self._ = self.request.getText
        self.cfg = self.request.cfg

        # Initialized on execute
        self.name = None

    def _wrap(self, macro_name, fn, args):
        """
        Parses arguments for a macro call and calls the macro
        function with the arguments.
        """
        if args:
            positional, keyword, trailing = \
                wikiutil.parse_quoted_separated(args)

            kwargs = {}
            nonascii = {}
            for kw in keyword:
                try:
                    kwargs[str(kw)] = keyword[kw]
                except UnicodeEncodeError:
                    nonascii[kw] = keyword[kw]

            # add trailing args as keyword argument if present,
            # otherwise remove if the user entered some
            # (so macros don't get a string where they expect a list)
            if trailing:
                kwargs['_trailing_args'] = trailing
            elif '_trailing_args' in kwargs:
                del kwargs['_trailing_args']

            # add nonascii args as keyword argument if present,
            # otherwise remove if the user entered some
            # (so macros don't get a string where they expect a list)
            if nonascii:
                kwargs['_non_ascii_kwargs'] = nonascii
            elif '_non_ascii_kwargs' in kwargs:
                del kwargs['_non_ascii_kwargs']

        else:
            positional = []
            kwargs = {}

        try:
            return fn(self, *positional, **kwargs)
        except (ValueError, TypeError), e:
            return self.format_error(e)

    def format_error(self, err):
        return u'[[%s: %s]]' % (self.name, str(err))

    def execute(self, macro_name, args):
        """ Get and execute a macro

        Try to get a plugin macro, or a builtin macro or a language
        macro, or just raise ImportError.
        """
        self.name = macro_name
        try:
            try:
                call = wikiutil.importPlugin(self.cfg, 'macro', macro_name,
                                             function='macro_%s' % macro_name)
                execute = lambda _self, _args: _self._wrap(macro_name, call, _args)
            except wikiutil.PluginAttributeError:
                execute = wikiutil.importPlugin(self.cfg, 'macro', macro_name)
        except wikiutil.PluginMissingError:
            try:
                call = getattr(self.__class__, 'macro_%s' % macro_name)
                execute = lambda _self, _args: _self._wrap(macro_name, call, _args)
            except AttributeError:
                if macro_name in i18n.wikiLanguages():
                    execute = builtins._m_lang
                else:
                    raise ImportError("Cannot load macro %s" % macro_name)
        return execute(self, args)

    def _m_lang(self, text):
        """ Set the current language for page content.

            Language macro are used in two ways:
             * [lang] - set the current language until next lang macro
             * [lang(text)] - insert text with specific lang inside page
        """
        if text:
            return (self.formatter.lang(1, self.name) +
                    self.formatter.text(text) +
                    self.formatter.lang(0, self.name))

        self.request.current_lang = self.name
        return ''

    def get_dependencies(self, macro_name):
        if macro_name in self.Dependencies:
            return self.Dependencies[macro_name]
        try:
            return wikiutil.importPlugin(self.request.cfg, 'macro',
                                         macro_name, 'Dependencies')
        except wikiutil.PluginError:
            return self.defaultDependency

    def macro_TitleSearch(self):
        from MoinMoin.macro.FullSearch import search_box
        return search_box("titlesearch", self)

    def macro_GoTo(self):
        """ Make a goto box

        @rtype: unicode
        @return: goto box html fragment
        """
        _ = self._
        html = [
            u'<form method="get" action="">',
            u'<div>',
            u'<input type="hidden" name="action" value="goto">',
            u'<input type="text" name="target" size="30">',
            u'<input type="submit" value="%s">' % _("Go To Page"),
            u'</div>',
            u'</form>',
            ]
        html = u'\n'.join(html)
        return self.formatter.rawHTML(html)

    def _make_index(self, word_re=u'.+'):
        """ make an index page (used for TitleIndex and WordIndex macro)

            word_re is a regex used for splitting a pagename into fragments
            matched by it (used for WordIndex). For TitleIndex, we just match
            the whole page name, so we only get one fragment that is the same
            as the pagename.

            TODO: _make_index could get a macro on its own, more powerful / less special than WordIndex and TitleIndex.
                  It should be able to filter for specific mimetypes, maybe match pagenames by regex (replace PageList?), etc.
        """
        _ = self._
        request = self.request
        fmt = self.formatter
        allpages = int(self.form.get('allpages', [0])[0]) != 0
        # Get page list readable by current user, filter by isSystemPage if needed
        if allpages:
            pages = request.rootpage.getPageList()
        else:
            def nosyspage(name):
                return not wikiutil.isSystemPage(request, name)
            pages = request.rootpage.getPageList(filter=nosyspage)

        word_re = re.compile(word_re, re.UNICODE)
        wordmap = {}
        for name in pages:
            for word in word_re.findall(name):
                try:
                    if not wordmap[word].count(name):
                        wordmap[word].append(name)
                except KeyError:
                    wordmap[word] = [name]

        # Sort ignoring case
        tmp = [(word.upper(), word) for word in wordmap]
        tmp.sort()
        all_words = [item[1] for item in tmp]

        index_letters = []
        current_letter = None
        output = []
        for word in all_words:
            letter = wikiutil.getUnicodeIndexGroup(word)
            if letter != current_letter:
                cssid = "idx" + wikiutil.quoteWikinameURL(letter).replace('%', '')
                output.append(fmt.heading(1, 2, id=cssid)) # fmt.anchordef didn't work
                output.append(fmt.text(letter.replace('~', 'Others')))
                output.append(fmt.heading(0, 2))
                current_letter = letter
            if letter not in index_letters:
                index_letters.append(letter)
            links = wordmap[word]
            if len(links) and links[0] != word: # show word fragment as on WordIndex
                output.append(fmt.strong(1))
                output.append(word)
                output.append(fmt.strong(0))

            output.append(fmt.bullet_list(1))
            links.sort()
            last_page = None
            for name in links:
                if name == last_page:
                    continue
                output.append(fmt.listitem(1))
                output.append(Page(request, name).link_to(request, attachment_indicator=1))
                output.append(fmt.listitem(0))
            output.append(fmt.bullet_list(0))

        def _make_index_key(index_letters):
            index_letters.sort()
            def letter_link(ch):
                cssid = "idx" + wikiutil.quoteWikinameURL(ch).replace('%', '')
                return fmt.anchorlink(1, cssid) + fmt.text(ch.replace('~', 'Others')) + fmt.anchorlink(0)
            links = [letter_link(letter) for letter in index_letters]
            return ' | '.join(links)

        page = fmt.page
        allpages_txt = (_('Include system pages'), _('Exclude system pages'))[allpages]
        allpages_url = page.url(request, querystr={'allpages': allpages and '0' or '1'}, relative=False)

        output = [fmt.paragraph(1), _make_index_key(index_letters), fmt.linebreak(0),
                  fmt.url(1, allpages_url), fmt.text(allpages_txt), fmt.url(0), fmt.paragraph(0)] + output
        return u''.join(output)


    def macro_TitleIndex(self):
        return self._make_index()

    def macro_WordIndex(self):
        if self.request.isSpiderAgent: # reduce bot cpu usage
            return ''
        word_re = u'[%s][%s]+' % (config.chars_upper, config.chars_lower)
        return self._make_index(word_re=word_re)


    def macro_PageList(self, needle=None):
        from MoinMoin import search
        _ = self._
        case = 0

        # If called with empty or no argument, default to regex search for .+, the full page list.
        needle = wikiutil.get_unicode(request, needle, 'needle', u'regex:.+')

        # With whitespace argument, return same error message as FullSearch
        if not needle.strip():
            err = _('Please use a more selective search term instead of {{{"%s"}}}') % needle
            return '<span class="error">%s</span>' % err

        # Return a title search for needle, sorted by name.
        results = search.searchPages(self.request, needle,
                titlesearch=1, case=case, sort='page_name')
        return results.pageList(self.request, self.formatter, paging=False)

    def macro_InterWiki(self):
        from StringIO import StringIO
        interwiki_list = wikiutil.load_wikimap(self.request)
        buf = StringIO()
        buf.write('<dl>')
        iwlist = interwiki_list.items() # this is where we cached it
        iwlist.sort()
        for tag, url in iwlist:
            buf.write('<dt><tt><a href="%s">%s</a></tt></dt>' % (
                wikiutil.join_wiki(url, 'RecentChanges'), tag))
            if '$PAGE' not in url:
                buf.write('<dd><tt><a href="%s">%s</a></tt></dd>' % (url, url))
            else:
                buf.write('<dd><tt>%s</tt></dd>' % url)
        buf.write('</dl>')
        return self.formatter.rawHTML(buf.getvalue())

    def macro_PageCount(self, exists=None):
        """ Return number of pages readable by current user

        Return either an exact count (slow!) or fast count including
        deleted pages.

        TODO: make macro syntax more sane
        """
        exists = wikiutil.get_unicode(self.request, exists, 'exists')
        # Check input
        only_existing = False
        if exists == u'exists':
            only_existing = True
        elif exists:
            # Wrong argument, return inline error message
            arg = self.formatter.text(args)
            return (self.formatter.span(1, css_class="error") +
                    'Wrong argument: %s' % arg +
                    self.formatter.span(0))

        count = self.request.rootpage.getPageCount(exists=only_existing)
        return self.formatter.text("%d" % count)

    def macro_Icon(self, icon):
        return self.formatter.icon(icon.lower())

    def macro_TemplateList(self, arg):
        _ = self._
        try:
            needle_re = re.compile(arg, re.IGNORECASE)
        except re.error, e:
            return "<strong>%s: %s</strong>" % (
                _("ERROR in regex '%s'") % (arg, ), e)

        # Get page list readable by current user, filtered by needle
        hits = self.request.rootpage.getPageList(filter=needle_re.search)
        hits.sort()

        result = []
        result.append(self.formatter.bullet_list(1))
        for pagename in hits:
            result.append(self.formatter.listitem(1))
            result.append(self.formatter.pagelink(1, pagename, generated=1))
            result.append(self.formatter.text(pagename))
            result.append(self.formatter.pagelink(0, pagename))
            result.append(self.formatter.listitem(0))
        result.append(self.formatter.bullet_list(0))
        return ''.join(result)


    def __get_Date(self, args, format_date):
        _ = self._
        if not args:
            tm = time.time() # always UTC
        elif len(args) >= 19 and args[4] == '-' and args[7] == '-' \
                and args[10] == 'T' and args[13] == ':' and args[16] == ':':
            # we ignore any time zone offsets here, assume UTC,
            # and accept (and ignore) any trailing stuff
            try:
                year, month, day = int(args[0:4]), int(args[5:7]), int(args[8:10])
                hour, minute, second = int(args[11:13]), int(args[14:16]), int(args[17:19])
                tz = args[19:] # +HHMM, -HHMM or Z or nothing (then we assume Z)
                tzoffset = 0 # we assume UTC no matter if there is a Z
                if tz:
                    sign = tz[0]
                    if sign in '+-':
                        tzh, tzm = int(tz[1:3]), int(tz[3:])
                        tzoffset = (tzh*60+tzm)*60
                        if sign == '-':
                            tzoffset = -tzoffset
                tm = (year, month, day, hour, minute, second, 0, 0, 0)
            except ValueError, e:
                return "<strong>%s: %s</strong>" % (
                    _("Bad timestamp '%s'") % (args, ), e)
            # as mktime wants a localtime argument (but we only have UTC),
            # we adjust by our local timezone's offset
            try:
                tm = time.mktime(tm) - time.timezone - tzoffset
            except (OverflowError, ValueError):
                tm = 0 # incorrect, but we avoid an ugly backtrace
        else:
            # try raw seconds since epoch in UTC
            try:
                tm = float(args)
            except ValueError, e:
                return "<strong>%s: %s</strong>" % (
                    _("Bad timestamp '%s'") % (args, ), e)
        return format_date(tm)

    def macro_Date(self, stamp=None):
        return self.__get_Date(stamp, self.request.user.getFormattedDate)

    def macro_DateTime(self, stamp=None):
        return self.__get_Date(stamp, self.request.user.getFormattedDateTime)

    def macro_Anchor(self, anchor):
        return self.formatter.anchordef(anchor or "anchor")

    def macro_MailTo(self, email, text=None):
        text = wikiutil.get_unicode(self.request, text, 'text', u'')
        from MoinMoin.mail.sendmail import decodeSpamSafeEmail

        if self.request.user.valid:
            # decode address and generate mailto: link
            email = decodeSpamSafeEmail(email)
            result = (self.formatter.url(1, 'mailto:' + email, css='mailto', do_escape=0) +
                      self.formatter.text(text or email) +
                      self.formatter.url(0))
        else:
            # unknown user, maybe even a spambot, so
            # just return text as given in macro args

            if text:
                result = self.formatter.text(text+" ")

            result += self.formatter.code(1) + \
                self.formatter.text("<%s>" % email) + \
                self.formatter.code(0)

        return result

    def macro_GetVal(self, page, key):
        d = self.request.dicts.dict(page)
        result = d.get(key, '')
        return self.formatter.text(result)

