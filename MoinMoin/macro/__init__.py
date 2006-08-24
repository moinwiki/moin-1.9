# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Macro Implementation

    These macros are used by the wiki parser module to implement complex
    and/or dynamic page content.

    The canonical interface to plugin macros is their execute() function,
    which gets passed an instance of the Macro class. Such an instance
    has the four members parser, formatter, form and request.

    Using "form" directly is deprecated and should be replaced by "request.form".

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport
modules = pysupport.getPackageModules(__file__)

import re, time, os
from MoinMoin import action, config, util
from MoinMoin import wikiutil, i18n
from MoinMoin.Page import Page
from MoinMoin.util import pysupport

names = ["TitleSearch", "WordIndex", "TitleIndex",
         "GoTo", "InterWiki", "PageCount", "UserPreferences",
         # Macros with arguments
         "Icon", "PageList", "Date", "DateTime", "Anchor", "MailTo", "GetVal",
         "TemplateList",
]

#############################################################################
### Helpers
#############################################################################

def getNames(cfg):
    if hasattr(cfg, 'macro_names'):
        return cfg.macro_names
    else:
        lnames = names[:]
        lnames.extend(i18n.wikiLanguages().keys())
        lnames.extend(wikiutil.getPlugins('macro', cfg))
        cfg.macro_names = lnames # remember it
        return lnames


#############################################################################
### Macros - Handlers for [[macroname]] markup
#############################################################################

class Macro:
    """ Macro handler 
    
    There are three kinds of macros: 
     * Builtin Macros - implemented in this file and named _macro_[name]
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
        "UserPreferences": ["time"],
        "Anchor": [],
        "Mailto": ["user"],
        "GetVal": ["pages"],
        "TemplateList": ["namespace"],
        }

    # we need the lang macros to execute when html is generated,
    # to have correct dir and lang html attributes
    for lang in i18n.wikiLanguages().keys():
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

    def execute(self, macro_name, args):
        """ Get and execute a macro 
        
        Try to get a plugin macro, or a builtin macro or a language
        macro, or just raise ImportError. 
        """
        self.name = macro_name
        try:
            execute = wikiutil.importPlugin(self.cfg, 'macro', macro_name)
        except wikiutil.PluginMissingError:
            try:
                builtins = self.__class__
                execute = getattr(builtins, '_macro_' + macro_name)
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

    def _macro_TitleSearch(self, args):
        from FullSearch import search_box
        return search_box("titlesearch", self)

    def _macro_GoTo(self, args):
        """ Make a goto box

        @param args: macro arguments
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

    def _make_index(self, args, word_re=u'.+'):
        """ make an index page (used for TitleIndex and WordIndex macro)

            word_re is a regex used for splitting a pagename into fragments
            matched by it (used for WordIndex). For TitleIndex, we just match
            the whole page name, so we only get one fragment that is the same
            as the pagename.

            TODO: later this can get a macro on its own, more powerful and less
                  special than WordIndex and TitleIndex.
                  It should be able to filter for specific mimetypes, maybe match
                  pagenames by regex (replace PageList?), etc.

                  it should use the formatter asap
        """
        _ = self._
        allpages = int(self.form.get('allpages', [0])[0]) != 0
        # Get page list readable by current user
        # Filter by isSystemPage if needed
        if allpages:
            # TODO: make this fast by caching full page list
            pages = self.request.rootpage.getPageList()
        else:
            def filter(name):
                return not wikiutil.isSystemPage(self.request, name)
            pages = self.request.rootpage.getPageList(filter=filter)

        word_re = re.compile(word_re, re.UNICODE)
        map = {}
        for name in pages:
            for word in word_re.findall(name):
                try:
                    if not map[word].count(name):
                        map[word].append(name)
                except KeyError:
                    map[word] = [name]

        # Sort ignoring case
        all_words = map.keys()
        tmp = [(word.upper(), word) for word in all_words]
        tmp.sort()
        all_words = [item[1] for item in tmp]

        index_letters = []
        current_letter = None
        html = []
        for word in all_words:
            letter = wikiutil.getUnicodeIndexGroup(word)
            if letter != current_letter:
                #html.append(self.formatter.anchordef()) # XXX no text param available!
                html.append(u'<a name="%s"><h2>%s</h2></a>' % (
                    wikiutil.quoteWikinameURL(letter), letter.replace('~', 'Others')))
                current_letter = letter
            if letter not in index_letters:
                index_letters.append(letter)
            links = map[word]
            if len(links) and links[0] != word: # show word fragment as on WordIndex
                html.append(self.formatter.strong(1))
                html.append(word)
                html.append(self.formatter.strong(0))

            html.append(self.formatter.bullet_list(1))
            links.sort()
            last_page = None
            for name in links:
                if name == last_page:
                    continue
                html.append(self.formatter.listitem(1))
                html.append(Page(self.request, name).link_to(self.request, attachment_indicator=1))
                html.append(self.formatter.listitem(0))
            html.append(self.formatter.bullet_list(0))

        def _make_index_key(index_letters, additional_html=''):
            index_letters.sort()
            def letter_link(ch):
                return '<a href="#%s">%s</a>' % (wikiutil.quoteWikinameURL(ch), ch.replace('~', 'Others'))
            links = [letter_link(letter) for letter in index_letters]
            return "<p>%s%s</p>" % (' | '.join(links), additional_html)

        page = self.formatter.page
        allpages_txt = (_('Include system pages'), _('Exclude system pages'))[allpages]
        allpages_link = page.link_to(self.request, allpages_txt, querystr={'allpages': allpages and '0' or '1'})
        index = _make_index_key(index_letters, u'<br>%s' % allpages_link)
        # ?action=titleindex and ?action=titleindex&mimetype=text/xml removed

        return u'%s%s' % (index, u''.join(html))


    def _macro_TitleIndex(self, args):
        return self._make_index(args)

    def _macro_WordIndex(self, args):
        word_re = u'[%s][%s]+' % (config.chars_upper, config.chars_lower)
        return self._make_index(args, word_re=word_re)


    def _macro_PageList(self, needle):
        from MoinMoin import search
        _ = self._
        literal = 0
        case = 0

        # If called with empty or no argument, default to regex search for .+, the full page list.
        if not needle:
            needle = 'regex:.+'

        # With whitespace argument, return same error message as FullSearch
        elif needle.isspace():
            err = _('Please use a more selective search term instead of {{{"%s"}}}') % needle
            return '<span class="error">%s</span>' % err

        # Return a title search for needle, sorted by name.
        # XXX: what's with literal?
        results = search.searchPages(self.request, needle,
                titlesearch=1, case=case, sort='page_name')
        return results.pageList(self.request, self.formatter, paging=False)

    def _macro_InterWiki(self, args):
        from StringIO import StringIO
        interwiki_list = wikiutil.load_wikimap(self.request)
        buf = StringIO()
        buf.write('<dl>')
        list = interwiki_list.items() # this is where we cached it
        list.sort()
        for tag, url in list:
            buf.write('<dt><tt><a href="%s">%s</a></tt></dt>' % (
                wikiutil.join_wiki(url, 'RecentChanges'), tag))
            if '$PAGE' not in url:
                buf.write('<dd><tt><a href="%s">%s</a></tt></dd>' % (url, url))
            else:
                buf.write('<dd><tt>%s</tt></dd>' % url)
        buf.write('</dl>')
        return self.formatter.rawHTML(buf.getvalue())

    def _macro_PageCount(self, args):
        """ Return number of pages readable by current user
        
        Return either an exact count (slow!) or fast count including
        deleted pages.
        """
        # Check input
        options = {None: 0, '': 0, 'exists': 1}
        try:
            exists = options[args]
        except KeyError:
            # Wrong argument, return inline error message
            arg = self.formatter.text(args)
            return (self.formatter.span(1, css_class="error") +
                    'Wrong argument: %s' % arg +
                    self.formatter.span(0))

        count = self.request.rootpage.getPageCount(exists=exists)
        return self.formatter.text("%d" % count)

    def _macro_Icon(self, args):
        icon = args.lower()
        return self.formatter.icon(icon)

    def _macro_TemplateList(self, args):
        _ = self._
        try:
            needle_re = re.compile(args or '', re.IGNORECASE)
        except re.error, e:
            return "<strong>%s: %s</strong>" % (
                _("ERROR in regex '%s'") % (args,), e)

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
                    _("Bad timestamp '%s'") % (args,), e)
            # as mktime wants a localtime argument (but we only have UTC),
            # we adjust by our local timezone's offset
            try:
                tm = time.mktime(tm) - time.timezone - tzoffset
            except (OverflowError, ValueError), err:
                tm = 0 # incorrect, but we avoid an ugly backtrace
        else:
            # try raw seconds since epoch in UTC
            try:
                tm = float(args)
            except ValueError, e:
                return "<strong>%s: %s</strong>" % (
                    _("Bad timestamp '%s'") % (args,), e)
        return format_date(tm)

    def _macro_Date(self, args):
        return self.__get_Date(args, self.request.user.getFormattedDate)

    def _macro_DateTime(self, args):
        return self.__get_Date(args, self.request.user.getFormattedDateTime)


    def _macro_UserPreferences(self, args):
        from MoinMoin import userform

        create_only = False
        if isinstance(args, unicode):
            args = args.strip(" '\"")
            create_only = (args.lower() == "createonly")

        return self.formatter.rawHTML(userform.getUserForm(
            self.request,
            create_only=create_only))

    def _macro_Anchor(self, args):
        return self.formatter.anchordef(args or "anchor")

    def _macro_MailTo(self, args):
        from MoinMoin.mail.sendmail import decodeSpamSafeEmail

        args = args or ''
        if ',' not in args:
            email = args
            text = ''
        else:
            email, text = args.split(',', 1)

        email, text = email.strip(), text.strip()

        if self.request.user.valid:
            # decode address and generate mailto: link
            email = decodeSpamSafeEmail(email)
            result = (self.formatter.url(1, 'mailto:' + email, css='mailto', do_escape=0) +
                      self.formatter.text(text or email) +
                      self.formatter.url(0))
        else:
            # unknown user, maybe even a spambot, so
            # just return text as given in macro args
            email = self.formatter.code(1) + \
                self.formatter.text("<%s>" % email) + \
                self.formatter.code(0)
            if text:
                result = self.formatter.text(text) + " " + email
            else:
                result = email

        return result

    def _macro_GetVal(self, args):
        page, key = args.split(',')
        d = self.request.dicts.dict(page)
        result = d.get(key, '')
        return self.formatter.text(result)

