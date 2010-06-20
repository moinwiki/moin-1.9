# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Theme Package

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import StringIO

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import i18n, wikiutil, config, version, caching
from MoinMoin.action import get_available_actions
from MoinMoin.Page import Page
from MoinMoin.util import pysupport

modules = pysupport.getPackageModules(__file__)

# Check whether we can emit a RSS feed.
# RSS is broken on plain Python 2.4.x, and works only when installing PyXML.
# News: A user reported that the RSS is valid when using Python 2.5.1 on Windows.
import sys, xml
rss_supported = sys.version_info[:3] >= (2, 5, 1) or '_xmlplus' in xml.__file__


class ThemeBase:
    """ Base class for themes

    This class supply all the standard template that sub classes can
    use without rewriting the same code. If you want to change certain
    elements, override them.
    """

    name = 'base'

    # fake _ function to get gettext recognize those texts:
    _ = lambda x: x

    # TODO: remove icons that are not used any more.
    icons = {
        # key         alt                        icon filename      w   h
        # ------------------------------------------------------------------
        # navibar
        'help':        ("%(page_help_contents)s", "moin-help.png",   12, 11),
        'find':        ("%(page_find_page)s",     "moin-search.png", 12, 12),
        'diff':        (_("Diffs"),               "moin-diff.png",   15, 11),
        'info':        (_("Info"),                "moin-info.png",   12, 11),
        'edit':        (_("Edit"),                "moin-edit.png",   12, 12),
        'unsubscribe': (_("Unsubscribe"),         "moin-unsubscribe.png", 14, 10),
        'subscribe':   (_("Subscribe"),           "moin-subscribe.png", 14, 10),
        'raw':         (_("Raw"),                 "moin-raw.png",    12, 13),
        'xml':         (_("XML"),                 "moin-xml.png",    20, 13),
        'print':       (_("Print"),               "moin-print.png",  16, 14),
        'view':        (_("View"),                "moin-show.png",   12, 13),
        'home':        (_("Home"),                "moin-home.png",   13, 12),
        'up':          (_("Up"),                  "moin-parent.png", 15, 13),
        # FileAttach
        'attach':     ("%(attach_count)s",       "moin-attach.png",  7, 15),
        'attachimg':  ("",                       "attach.png",      32, 32),
        # RecentChanges
        'rss':        (_("[RSS]"),               "moin-rss.png",    24, 24),
        'deleted':    (_("[DELETED]"),           "moin-deleted.png", 60, 12),
        'updated':    (_("[UPDATED]"),           "moin-updated.png", 60, 12),
        'renamed':    (_("[RENAMED]"),           "moin-renamed.png", 60, 12),
        'conflict':   (_("[CONFLICT]"),          "moin-conflict.png", 60, 12),
        'new':        (_("[NEW]"),               "moin-new.png",    31, 12),
        'diffrc':     (_("[DIFF]"),              "moin-diff.png",   15, 11),
        # General
        'bottom':     (_("[BOTTOM]"),            "moin-bottom.png", 14, 10),
        'top':        (_("[TOP]"),               "moin-top.png",    14, 10),
        'www':        ("[WWW]",                  "moin-www.png",    11, 11),
        'mailto':     ("[MAILTO]",               "moin-email.png",  14, 10),
        'news':       ("[NEWS]",                 "moin-news.png",   10, 11),
        'telnet':     ("[TELNET]",               "moin-telnet.png", 10, 11),
        'ftp':        ("[FTP]",                  "moin-ftp.png",    11, 11),
        'file':       ("[FILE]",                 "moin-ftp.png",    11, 11),
        # search forms
        'searchbutton': ("[?]",                  "moin-search.png", 12, 12),
        'interwiki':  ("[%(wikitag)s]",          "moin-inter.png",  16, 16),

        # smileys (this is CONTENT, but good looking smileys depend on looking
        # adapted to the theme background color and theme style in general)
        #vvv    ==      vvv  this must be the same for GUI editor converter
        'X-(':        ("X-(",                    'angry.png',       15, 15),
        ':D':         (":D",                     'biggrin.png',     15, 15),
        '<:(':        ("<:(",                    'frown.png',       15, 15),
        ':o':         (":o",                     'redface.png',     15, 15),
        ':(':         (":(",                     'sad.png',         15, 15),
        ':)':         (":)",                     'smile.png',       15, 15),
        'B)':         ("B)",                     'smile2.png',      15, 15),
        ':))':        (":))",                    'smile3.png',      15, 15),
        ';)':         (";)",                     'smile4.png',      15, 15),
        '/!\\':       ("/!\\",                   'alert.png',       15, 15),
        '<!>':        ("<!>",                    'attention.png',   15, 15),
        '(!)':        ("(!)",                    'idea.png',        15, 15),

        # copied 2001-11-16 from http://pikie.darktech.org/cgi/pikie.py?EmotIcon
        ':-?':        (":-?",                    'tongue.png',      15, 15),
        ':\\':        (":\\",                    'ohwell.png',      15, 15),
        '>:>':        (">:>",                    'devil.png',       15, 15),
        '|)':         ("|)",                     'tired.png',       15, 15),

        # some folks use noses in their emoticons
        ':-(':        (":-(",                    'sad.png',         15, 15),
        ':-)':        (":-)",                    'smile.png',       15, 15),
        'B-)':        ("B-)",                    'smile2.png',      15, 15),
        ':-))':       (":-))",                   'smile3.png',      15, 15),
        ';-)':        (";-)",                    'smile4.png',      15, 15),
        '|-)':        ("|-)",                    'tired.png',       15, 15),

        # version 1.0
        '(./)':       ("(./)",                   'checkmark.png',   20, 15),
        '{OK}':       ("{OK}",                   'thumbs-up.png',   14, 12),
        '{X}':        ("{X}",                    'icon-error.png',  16, 16),
        '{i}':        ("{i}",                    'icon-info.png',   16, 16),
        '{1}':        ("{1}",                    'prio1.png',       15, 13),
        '{2}':        ("{2}",                    'prio2.png',       15, 13),
        '{3}':        ("{3}",                    'prio3.png',       15, 13),

        # version 1.3.4 (stars)
        # try {*}{*}{o}
        '{*}':        ("{*}",                    'star_on.png',     15, 15),
        '{o}':        ("{o}",                    'star_off.png',    15, 15),
    }
    del _

    # Style sheets - usually there is no need to override this in sub
    # classes. Simply supply the css files in the css directory.

    # Standard set of style sheets
    stylesheets = (
        # media         basename
        ('all',         'common'),
        ('screen',      'screen'),
        ('print',       'print'),
        ('projection',  'projection'),
        )

    # Used in print mode
    stylesheets_print = (
        # media         basename
        ('all',         'common'),
        ('all',         'print'),
        )

    # Used in slide show mode
    stylesheets_projection = (
        # media         basename
        ('all',         'common'),
        ('all',         'projection'),
       )

    stylesheetsCharset = 'utf-8'

    def __init__(self, request):
        """
        Initialize the theme object.

        @param request: the request object
        """
        self.request = request
        self.cfg = request.cfg
        self._cache = {} # Used to cache elements that may be used several times
        self._status = []
        self._send_title_called = False

    def img_url(self, img):
        """ Generate an image href

        @param img: the image filename
        @rtype: string
        @return: the image href
        """
        return "%s/%s/img/%s" % (self.cfg.url_prefix_static, self.name, img)

    def emit_custom_html(self, html):
        """
        generate custom HTML code in `html`

        @param html: a string or a callable object, in which case
                     it is called and its return value is used
        @rtype: string
        @return: string with html
        """
        if html:
            if callable(html):
                html = html(self.request)
        return html

    def logo(self):
        """ Assemble logo with link to front page

        The logo contain an image and or text or any html markup the
        admin inserted in the config file. Everything it enclosed inside
        a div with id="logo".

        @rtype: unicode
        @return: logo html
        """
        html = u''
        if self.cfg.logo_string:
            page = wikiutil.getFrontPage(self.request)
            logo = page.link_to_raw(self.request, self.cfg.logo_string)
            html = u'''<div id="logo">%s</div>''' % logo
        return html

    def interwiki(self, d):
        """ Assemble the interwiki name display, linking to page_front_page

        @param d: parameter dictionary
        @rtype: string
        @return: interwiki html
        """
        if self.request.cfg.show_interwiki:
            page = wikiutil.getFrontPage(self.request)
            text = self.request.cfg.interwikiname or u'Self'
            link = page.link_to(self.request, text=text, rel='nofollow')
            html = u'<div id="interwiki"><span>%s</span></div>' % link
        else:
            html = u''
        return html

    def title(self, d):
        """ Assemble the title (now using breadcrumbs)

        @param d: parameter dictionary
        @rtype: string
        @return: title html
        """
        _ = self.request.getText
        content = []
        if d['title_text'] == d['page'].split_title(): # just showing a page, no action
            curpage = ''
            segments = d['page_name'].split('/') # was: title_text
            for s in segments[:-1]:
                curpage += s
                content.append("<li>%s</li>" % Page(self.request, curpage).link_to(self.request, s))
                curpage += '/'
            link_text = segments[-1]
            link_title = _('Click to do a full-text search for this title')
            link_query = {
                'action': 'fullsearch',
                'value': 'linkto:"%s"' % d['page_name'],
                'context': '180',
            }
            # we dont use d['title_link'] any more, but make it ourselves:
            link = d['page'].link_to(self.request, link_text, querystr=link_query, title=link_title, css_class='backlink', rel='nofollow')
            content.append(('<li>%s</li>') % link)
        else:
            content.append('<li>%s</li>' % wikiutil.escape(d['title_text']))

        html = '''
<ul id="pagelocation">
%s
</ul>
''' % "".join(content)
        return html

    def title_with_separators(self, d):
        """ Assemble the title using slashes, not <ul>

        @param d: parameter dictionary
        @rtype: string
        @return: title html
        """
        _ = self.request.getText
        if d['title_text'] == d['page'].split_title():
            # just showing a page, no action
            segments = d['page_name'].split('/')
            link_text = segments[-1]
            link_title = _('Click to do a full-text search for this title')
            link_query = {'action': 'fullsearch', 'context': '180',
                          'value': 'linkto:"%s"' % d['page_name'], }
            link = d['page'].link_to(self.request, link_text,
                                     querystr=link_query, title=link_title,
                                     css_class='backlink', rel='nofollow')
            if len(segments) <= 1:
                html = link
            else:
                content = []
                curpage = ''
                for s in segments[:-1]:
                    curpage += s
                    content.append(Page(self.request,
                                        curpage).link_to(self.request, s))
                    curpage += '/'
                path_html = u'<span class="sep">/</span>'.join(content)
                html = u'<span class="pagepath">%s</span><span class="sep">/</span>%s' % (path_html, link)
        else:
            html = wikiutil.escape(d['title_text'])
        return u'<span id="pagelocation">%s</span>' % html

    def username(self, d):
        """ Assemble the username / userprefs link

        @param d: parameter dictionary
        @rtype: unicode
        @return: username html
        """
        request = self.request
        _ = request.getText

        userlinks = []
        # Add username/homepage link for registered users. We don't care
        # if it exists, the user can create it.
        if request.user.valid and request.user.name:
            interwiki = wikiutil.getInterwikiHomePage(request)
            name = request.user.name
            aliasname = request.user.aliasname
            if not aliasname:
                aliasname = name
            title = "%s @ %s" % (aliasname, interwiki[0])
            # link to (interwiki) user homepage
            homelink = (request.formatter.interwikilink(1, title=title, id="userhome", generated=True, *interwiki) +
                        request.formatter.text(name) +
                        request.formatter.interwikilink(0, title=title, id="userhome", *interwiki))
            userlinks.append(homelink)
            # link to userprefs action
            if 'userprefs' not in self.request.cfg.actions_excluded:
                userlinks.append(d['page'].link_to(request, text=_('Settings'),
                                               querystr={'action': 'userprefs'}, id='userprefs', rel='nofollow'))

        if request.user.valid:
            if request.user.auth_method in request.cfg.auth_can_logout:
                userlinks.append(d['page'].link_to(request, text=_('Logout'),
                                                   querystr={'action': 'logout', 'logout': 'logout'}, id='logout', rel='nofollow'))
        else:
            query = {'action': 'login'}
            # special direct-login link if the auth methods want no input
            if request.cfg.auth_login_inputs == ['special_no_input']:
                query['login'] = '1'
            if request.cfg.auth_have_login:
                userlinks.append(d['page'].link_to(request, text=_("Login"),
                                                   querystr=query, id='login', rel='nofollow'))

        userlinks = [u'<li>%s</li>' % link for link in userlinks]
        html = u'<ul id="username">%s</ul>' % ''.join(userlinks)
        return html

    def splitNavilink(self, text, localize=1):
        """ Split navibar links into pagename, link to page

        Admin or user might want to use shorter navibar items by using
        the [[page|title]] or [[url|title]] syntax. In this case, we don't
        use localization, and the links goes to page or to the url, not
        the localized version of page.

        Supported syntax:
            * PageName
            * WikiName:PageName
            * wiki:WikiName:PageName
            * url
            * all targets as seen above with title: [[target|title]]

        @param text: the text used in config or user preferences
        @rtype: tuple
        @return: pagename or url, link to page or url
        """
        request = self.request
        fmt = request.formatter
        title = None

        # Handle [[pagename|title]] or [[url|title]] formats
        if text.startswith('[[') and text.endswith(']]'):
            text = text[2:-2]
            try:
                pagename, title = text.split('|', 1)
                pagename = pagename.strip()
                title = title.strip()
                localize = 0
            except (ValueError, TypeError):
                # Just use the text as is.
                pagename = text.strip()
        else:
            pagename = text

        if wikiutil.is_URL(pagename):
            if not title:
                title = pagename
            link = fmt.url(1, pagename) + fmt.text(title) + fmt.url(0)
            return pagename, link

        # remove wiki: url prefix
        if pagename.startswith("wiki:"):
            pagename = pagename[5:]

        # try handling interwiki links
        try:
            interwiki, page = wikiutil.split_interwiki(pagename)
            thiswiki = request.cfg.interwikiname
            if interwiki == thiswiki or interwiki == 'Self':
                pagename = page
            else:
                if not title:
                    title = page
                link = fmt.interwikilink(True, interwiki, page) + fmt.text(title) + fmt.interwikilink(False, interwiki, page)
                return pagename, link
        except ValueError:
            pass

        # Handle regular pagename like "FrontPage"
        pagename = wikiutil.normalize_pagename(pagename, request.cfg)

        # Use localized pages for the current user
        if localize:
            page = wikiutil.getLocalizedPage(request, pagename)
        else:
            page = Page(request, pagename)

        pagename = page.page_name # can be different, due to i18n

        if not title:
            title = page.split_title()
            title = self.shortenPagename(title)

        link = page.link_to(request, title)

        return pagename, link

    def shortenPagename(self, name):
        """ Shorten page names

        Shorten very long page names that tend to break the user
        interface. The short name is usually fine, unless really stupid
        long names are used (WYGIWYD).

        If you don't like to do this in your theme, or want to use
        different algorithm, override this method.

        @param name: page name, unicode
        @rtype: unicode
        @return: shortened version.
        """
        maxLength = self.maxPagenameLength()
        # First use only the sub page name, that might be enough
        if len(name) > maxLength:
            name = name.split('/')[-1]
            # If it's not enough, replace the middle with '...'
            if len(name) > maxLength:
                half, left = divmod(maxLength - 3, 2)
                name = u'%s...%s' % (name[:half + left], name[-half:])
        return name

    def maxPagenameLength(self):
        """ Return maximum length for shortened page names """
        return 25

    def navibar(self, d):
        """ Assemble the navibar

        @param d: parameter dictionary
        @rtype: unicode
        @return: navibar html
        """
        request = self.request
        found = {} # pages we found. prevent duplicates
        items = [] # navibar items
        item = u'<li class="%s">%s</li>'
        current = d['page_name']

        # Process config navi_bar
        if request.cfg.navi_bar:
            for text in request.cfg.navi_bar:
                pagename, link = self.splitNavilink(text)
                if pagename == current:
                    cls = 'wikilink current'
                else:
                    cls = 'wikilink'
                items.append(item % (cls, link))
                found[pagename] = 1

        # Add user links to wiki links, eliminating duplicates.
        userlinks = request.user.getQuickLinks()
        for text in userlinks:
            # Split text without localization, user knows what he wants
            pagename, link = self.splitNavilink(text, localize=0)
            if not pagename in found:
                if pagename == current:
                    cls = 'userlink current'
                else:
                    cls = 'userlink'
                items.append(item % (cls, link))
                found[pagename] = 1

        # Add current page at end of local pages
        if not current in found:
            title = d['page'].split_title()
            title = self.shortenPagename(title)
            link = d['page'].link_to(request, title)
            cls = 'current'
            items.append(item % (cls, link))

        # Add sister pages.
        for sistername, sisterurl in request.cfg.sistersites:
            if sistername == request.cfg.interwikiname: # it is THIS wiki
                cls = 'sisterwiki current'
                items.append(item % (cls, sistername))
            else:
                # TODO optimize performance
                cache = caching.CacheEntry(request, 'sisters', sistername, 'farm', use_pickle=True)
                if cache.exists():
                    data = cache.content()
                    sisterpages = data['sisterpages']
                    if current in sisterpages:
                        cls = 'sisterwiki'
                        url = sisterpages[current]
                        link = request.formatter.url(1, url) + \
                               request.formatter.text(sistername) +\
                               request.formatter.url(0)
                        items.append(item % (cls, link))

        # Assemble html
        items = u''.join(items)
        html = u'''
<ul id="navibar">
%s
</ul>
''' % items
        return html

    def get_icon(self, icon):
        """ Return icon data from self.icons

        If called from <<Icon(file)>> we have a filename, not a
        key. Using filenames is deprecated, but for now, we simulate old
        behavior.

        @param icon: icon name or file name (string)
        @rtype: tuple
        @return: alt (unicode), href (string), width, height (int)
        """
        if icon in self.icons:
            alt, icon, w, h = self.icons[icon]
        else:
            # Create filenames to icon data mapping on first call, then
            # cache in class for next calls.
            if not getattr(self.__class__, 'iconsByFile', None):
                d = {}
                for data in self.icons.values():
                    d[data[1]] = data
                self.__class__.iconsByFile = d

            # Try to get icon data by file name
            if icon in self.iconsByFile:
                alt, icon, w, h = self.iconsByFile[icon]
            else:
                alt, icon, w, h = '', icon, '', ''

        return alt, self.img_url(icon), w, h

    def make_icon(self, icon, vars=None, **kw):
        """
        This is the central routine for making <img> tags for icons!
        All icons stuff except the top left logo and search field icons are
        handled here.

        @param icon: icon id (dict key)
        @param vars: ...
        @rtype: string
        @return: icon html (img tag)
        """
        if vars is None:
            vars = {}
        alt, img, w, h = self.get_icon(icon)
        try:
            alt = vars['icon-alt-text'] # if it is possible we take the alt-text from 'page_icons_table'
        except KeyError, err:
            try:
                alt = alt % vars # if not we just leave the  alt-text from 'icons'
            except KeyError, err:
                alt = 'KeyError: %s' % str(err)
        alt = self.request.getText(alt)
        tag = self.request.formatter.image(src=img, alt=alt, width=w, height=h, **kw)
        return tag

    def make_iconlink(self, which, d):
        """
        Make a link with an icon

        @param which: icon id (dictionary key)
        @param d: parameter dictionary
        @rtype: string
        @return: html link tag
        """
        qs = {}
        pagekey, querystr, title, icon = self.cfg.page_icons_table[which]
        qs.update(querystr) # do not modify the querystr dict in the cfg!
        d['icon-alt-text'] = d['title'] = title % d
        d['i18ntitle'] = self.request.getText(d['title'])
        img_src = self.make_icon(icon, d)
        rev = d['rev']
        if rev and which in ['raw', 'print', ]:
            qs['rev'] = str(rev)
        attrs = {'rel': 'nofollow', 'title': d['i18ntitle'], }
        page = d[pagekey]
        if isinstance(page, unicode):
            # e.g. d['page_parent_page'] is just the unicode pagename
            # while d['page'] will give a page object
            page = Page(self.request, page)
        return page.link_to_raw(self.request, text=img_src, querystr=qs, **attrs)

    def msg(self, d):
        """ Assemble the msg display

        Display a message with a widget or simple strings with a clear message link.

        @param d: parameter dictionary
        @rtype: unicode
        @return: msg display html
        """
        _ = self.request.getText
        msgs = d['msg']

        result = u""
        close = d['page'].link_to(self.request, text=_('Clear message'), css_class="clear-link")
        for msg, msg_class in msgs:
            try:
                result += u'<p>%s</p>' % msg.render()
                close = ''
            except AttributeError:
                if msg and msg_class:
                    result += u'<p><div class="%s">%s</div></p>' % (msg_class, msg)
                elif msg:
                    result += u'<p>%s</p>\n' % msg
        if result:
            html = result + close
            return u'<div id="message">\n%s\n</div>\n' % html
        else:
            return u''

        return u'<div id="message">\n%s\n</div>\n' % html

    def trail(self, d):
        """ Assemble page trail

        @param d: parameter dictionary
        @rtype: unicode
        @return: trail html
        """
        request = self.request
        user = request.user
        html = ''
        if not user.valid or user.show_page_trail:
            trail = user.getTrail()
            if trail:
                items = []
                for pagename in trail:
                    try:
                        interwiki, page = wikiutil.split_interwiki(pagename)
                        if interwiki != request.cfg.interwikiname and interwiki != 'Self':
                            link = (self.request.formatter.interwikilink(True, interwiki, page) +
                                    self.shortenPagename(page) +
                                    self.request.formatter.interwikilink(False, interwiki, page))
                            items.append('<li>%s</li>' % link)
                            continue
                        else:
                            pagename = page

                    except ValueError:
                        pass
                    page = Page(request, pagename)
                    title = page.split_title()
                    title = self.shortenPagename(title)
                    link = page.link_to(request, title)
                    items.append('<li>%s</li>' % link)
                html = '''
<ul id="pagetrail">
%s
</ul>''' % ''.join(items)
        return html

    def _stylesheet_link(self, theme, media, href, title=None):
        """
        Create a link tag for a stylesheet.

        @param theme: True: href gives the basename of a theme stylesheet,
                      False: href is a full url of a user/admin defined stylesheet.
        @param media: 'all', 'screen', 'print', 'projection', ...
        @param href: see param theme
        @param title: optional title (for alternate stylesheets), see
                      http://www.w3.org/Style/Examples/007/alternatives
        @rtype: string
        @return: stylesheet link html
        """
        if theme:
            href = '%s/%s/css/%s.css' % (self.cfg.url_prefix_static, self.name, href)
        attrs = 'type="text/css" charset="%s" media="%s" href="%s"' % (
                self.stylesheetsCharset, media, href, )
        if title:
            return '<link rel="alternate stylesheet" %s title="%s">' % (attrs, title)
        else:
            return '<link rel="stylesheet" %s>' % attrs

    def html_stylesheets(self, d):
        """ Assemble html head stylesheet links

        @param d: parameter dictionary
        @rtype: string
        @return: stylesheets links
        """
        request = self.request
        # Check mode
        if d.get('print_mode'):
            media = d.get('media', 'print')
            stylesheets = getattr(self, 'stylesheets_' + media)
        else:
            stylesheets = self.stylesheets

        theme_css = [self._stylesheet_link(True, *stylesheet) for stylesheet in stylesheets]
        cfg_css = [self._stylesheet_link(False, *stylesheet) for stylesheet in request.cfg.stylesheets]

        msie_css = """
<!-- css only for MS IE6/IE7 browsers -->
<!--[if lt IE 8]>
   %s
<![endif]-->
""" % self._stylesheet_link(True, 'all', 'msie')

        # Add user css url (assuming that user css uses same charset)
        href = request.user.valid and request.user.css_url
        if href and href.lower() != "none":
            user_css = self._stylesheet_link(False, 'all', href)
        else:
            user_css = ''

        return '\n'.join(theme_css + cfg_css + [msie_css, user_css])

    def shouldShowPageinfo(self, page):
        """ Should we show page info?

        Should be implemented by actions. For now, we check here by action
        name and page.

        @param page: current page
        @rtype: bool
        @return: true if should show page info
        """
        if page.exists() and self.request.user.may.read(page.page_name):
            # These  actions show the  page content.
            # TODO: on new action, page info will not show.
            # A better solution will be if the action itself answer the question: showPageInfo().
            contentActions = [u'', u'show', u'refresh', u'preview', u'diff',
                              u'subscribe', u'RenamePage', u'CopyPage', u'DeletePage',
                              u'SpellCheck', u'print']
            return self.request.action in contentActions
        return False

    def pageinfo(self, page):
        """ Return html fragment with page meta data

        Since page information uses translated text, it uses the ui
        language and direction. It looks strange sometimes, but
        translated text using page direction looks worse.

        @param page: current page
        @rtype: unicode
        @return: page last edit information
        """
        _ = self.request.getText
        html = ''
        if self.shouldShowPageinfo(page):
            info = page.lastEditInfo()
            if info:
                if info['editor']:
                    info = _("last edited %(time)s by %(editor)s") % info
                else:
                    info = _("last modified %(time)s") % info
                pagename = page.page_name
                if self.request.cfg.show_interwiki:
                    pagename = "%s: %s" % (self.request.cfg.interwikiname, pagename)
                info = "%s  (%s)" % (wikiutil.escape(pagename), info)
                html = '<p id="pageinfo" class="info"%(lang)s>%(info)s</p>\n' % {
                    'lang': self.ui_lang_attr(),
                    'info': info
                    }
        return html

    def searchform(self, d):
        """
        assemble HTML code for the search forms

        @param d: parameter dictionary
        @rtype: unicode
        @return: search form html
        """
        _ = self.request.getText
        form = self.request.values
        updates = {
            'search_label': _('Search:'),
            'search_value': wikiutil.escape(form.get('value', ''), 1),
            'search_full_label': _('Text'),
            'search_title_label': _('Titles'),
            'url': self.request.href(d['page'].page_name)
            }
        d.update(updates)

        html = u'''
<form id="searchform" method="get" action="%(url)s">
<div>
<input type="hidden" name="action" value="fullsearch">
<input type="hidden" name="context" value="180">
<label for="searchinput">%(search_label)s</label>
<input id="searchinput" type="text" name="value" value="%(search_value)s" size="20"
    onfocus="searchFocus(this)" onblur="searchBlur(this)"
    onkeyup="searchChange(this)" onchange="searchChange(this)" alt="Search">
<input id="titlesearch" name="titlesearch" type="submit"
    value="%(search_title_label)s" alt="Search Titles">
<input id="fullsearch" name="fullsearch" type="submit"
    value="%(search_full_label)s" alt="Search Full Text">
</div>
</form>
<script type="text/javascript">
<!--// Initialize search form
var f = document.getElementById('searchform');
f.getElementsByTagName('label')[0].style.display = 'none';
var e = document.getElementById('searchinput');
searchChange(e);
searchBlur(e);
//-->
</script>
''' % d
        return html

    def showversion(self, d, **keywords):
        """
        assemble HTML code for copyright and version display

        @param d: parameter dictionary
        @rtype: string
        @return: copyright and version display html
        """
        html = ''
        if self.cfg.show_version and not keywords.get('print_mode', 0):
            html = (u'<div id="version">MoinMoin Release %s [Revision %s], '
                     'Copyright by Juergen Hermann et al.</div>') % (version.release, version.revision, )
        return html

    def headscript(self, d):
        """ Return html head script with common functions

        @param d: parameter dictionary
        @rtype: unicode
        @return: script for html head
        """
        # Don't add script for print view
        if self.request.action == 'print':
            return u''

        _ = self.request.getText
        script = u"""
<script type="text/javascript">
<!--
var search_hint = "%(search_hint)s";
//-->
</script>
""" % {
    'search_hint': _('Search'),
    }
        return script

    def shouldUseRSS(self, page):
        """ Return True if RSS feature is available and we are on the
            RecentChanges page, or False.

            Currently rss is broken on plain Python, and works only when
            installing PyXML. Return true if PyXML is installed.
        """
        if not rss_supported:
            return False
        return page.page_name == u'RecentChanges' or \
           page.page_name == self.request.getText(u'RecentChanges')

    def rsshref(self, page):
        """ Create rss href, used for rss button and head link

        @rtype: unicode
        @return: rss href
        """
        request = self.request
        url = page.url(request, querystr={
                'action': 'rss_rc', 'ddiffs': '1', 'unique': '1', }, escape=0)
        return url

    def rsslink(self, d):
        """ Create rss link in head, used by FireFox

        RSS link for FireFox. This shows an rss link in the bottom of
        the page and let you subscribe to the wiki rss feed.

        @rtype: unicode
        @return: html head
        """
        link = u''
        page = d['page']
        if self.shouldUseRSS(page):
            link = (u'<link rel="alternate" title="%s Recent Changes" '
                    u'href="%s" type="application/rss+xml">') % (
                        wikiutil.escape(self.cfg.sitename, True),
                        wikiutil.escape(self.rsshref(page), True) )
        return link

    def html_head(self, d):
        """ Assemble html head

        @param d: parameter dictionary
        @rtype: unicode
        @return: html head
        """
        html = [
            u'<title>%(title)s - %(sitename)s</title>' % {
                'title': wikiutil.escape(d['title']),
                'sitename': wikiutil.escape(d['sitename']),
            },
            self.externalScript('common'),
            self.headscript(d), # Should move to separate .js file
            self.guiEditorScript(d),
            self.html_stylesheets(d),
            self.rsslink(d),
            self.universal_edit_button(d),
            ]
        return '\n'.join(html)

    def externalScript(self, name):
        """ Format external script html """
        src = '%s/common/js/%s.js' % (self.request.cfg.url_prefix_static, name)
        return '<script type="text/javascript" src="%s"></script>' % src

    def universal_edit_button(self, d, **keywords):
        """ Generate HTML for an edit link in the header."""
        page = d['page']
        if 'edit' in self.request.cfg.actions_excluded:
            return ""
        if not (page.isWritable() and
                self.request.user.may.write(page.page_name)):
            return ""
        _ = self.request.getText
        querystr = {'action': 'edit'}
        text = _(u'Edit')
        url = page.url(self.request, querystr=querystr, escape=0)
        return (u'<link rel="alternate" type="application/wiki" '
                u'title="%s" href="%s">' % (text, url))

    def credits(self, d, **keywords):
        """ Create credits html from credits list """
        if isinstance(self.cfg.page_credits, (list, tuple)):
            items = ['<li>%s</li>' % i for i in self.cfg.page_credits]
            html = '<ul id="credits">\n%s\n</ul>\n' % ''.join(items)
        else:
            # Old config using string, output as is
            html = self.cfg.page_credits
        return html

    def actionsMenu(self, page):
        """ Create actions menu list and items data dict

        The menu will contain the same items always, but items that are
        not available will be disabled (some broken browsers will let
        you select disabled options though).

        The menu should give best user experience for javascript
        enabled browsers, and acceptable behavior for those who prefer
        not to use Javascript.

        TODO: Move actionsMenuInit() into body onload - requires that the theme will render body,
              it is currently done in wikiutil/page.

        @param page: current page, Page object
        @rtype: unicode
        @return: actions menu html fragment
        """
        request = self.request
        _ = request.getText
        rev = request.rev

        menu = [
            'raw',
            'print',
            'RenderAsDocbook',
            'refresh',
            '__separator__',
            'SpellCheck',
            'LikePages',
            'LocalSiteMap',
            '__separator__',
            'RenamePage',
            'CopyPage',
            'DeletePage',
            '__separator__',
            'MyPages',
            'SubscribeUser',
            '__separator__',
            'Despam',
            'revert',
            'PackagePages',
            'SyncPages',
            ]

        titles = {
            # action: menu title
            '__title__': _("More Actions:"),
            # Translation may need longer or shorter separator
            '__separator__': _('------------------------'),
            'raw': _('Raw Text'),
            'print': _('Print View'),
            'refresh': _('Delete Cache'),
            'SpellCheck': _('Check Spelling'), # rename action!
            'RenamePage': _('Rename Page'),
            'CopyPage': _('Copy Page'),
            'DeletePage': _('Delete Page'),
            'LikePages': _('Like Pages'),
            'LocalSiteMap': _('Local Site Map'),
            'MyPages': _('My Pages'),
            'SubscribeUser': _('Subscribe User'),
            'Despam': _('Remove Spam'),
            'revert': _('Revert to this revision'),
            'PackagePages': _('Package Pages'),
            'RenderAsDocbook': _('Render as Docbook'),
            'SyncPages': _('Sync Pages'),
            }

        options = []
        option = '<option value="%(action)s"%(disabled)s>%(title)s</option>'
        # class="disabled" is a workaround for browsers that ignore
        # "disabled", e.g IE, Safari
        # for XHTML: data['disabled'] = ' disabled="disabled"'
        disabled = ' disabled class="disabled"'

        # Format standard actions
        available = get_available_actions(request.cfg, page, request.user)
        for action in menu:
            data = {'action': action, 'disabled': '', 'title': titles[action]}
            # removes excluded actions from the more actions menu
            if action in request.cfg.actions_excluded:
                continue

            # Enable delete cache only if page can use caching
            if action == 'refresh':
                if not page.canUseCache():
                    data['action'] = 'show'
                    data['disabled'] = disabled

            # revert action enabled only if user can revert
            if action == 'revert' and not request.user.may.revert(page.page_name):
                data['action'] = 'show'
                data['disabled'] = disabled

            # SubscribeUser action enabled only if user has admin rights
            if action == 'SubscribeUser' and not request.user.may.admin(page.page_name):
                data['action'] = 'show'
                data['disabled'] = disabled

            # Despam action enabled only for superusers
            if action == 'Despam' and not request.user.isSuperUser():
                data['action'] = 'show'
                data['disabled'] = disabled

            # Special menu items. Without javascript, executing will
            # just return to the page.
            if action.startswith('__'):
                data['action'] = 'show'

            # Actions which are not available for this wiki, user or page
            if (action == '__separator__' or
                (action[0].isupper() and not action in available)):
                data['disabled'] = disabled

            options.append(option % data)

        # Add custom actions not in the standard menu, except for
        # some actions like AttachFile (we have them on top level)
        more = [item for item in available if not item in titles and not item in ('AttachFile', )]
        more.sort()
        if more:
            # Add separator
            separator = option % {'action': 'show', 'disabled': disabled,
                                  'title': titles['__separator__']}
            options.append(separator)
            # Add more actions (all enabled)
            for action in more:
                data = {'action': action, 'disabled': ''}
                # Always add spaces: AttachFile -> Attach File
                # XXX do not create page just for using split_title -
                # creating pages for non-existent does 2 storage lookups
                #title = Page(request, action).split_title(force=1)
                title = action
                # Use translated version if available
                data['title'] = _(title)
                options.append(option % data)

        data = {
            'label': titles['__title__'],
            'options': '\n'.join(options),
            'rev_field': rev and '<input type="hidden" name="rev" value="%d">' % rev or '',
            'do_button': _("Do"),
            'url': self.request.href(page.page_name)
            }
        html = '''
<form class="actionsmenu" method="GET" action="%(url)s">
<div>
    <label>%(label)s</label>
    <select name="action"
        onchange="if ((this.selectedIndex != 0) &&
                      (this.options[this.selectedIndex].disabled == false)) {
                this.form.submit();
            }
            this.selectedIndex = 0;">
        %(options)s
    </select>
    <input type="submit" value="%(do_button)s">
    %(rev_field)s
</div>
<script type="text/javascript">
<!--// Init menu
actionsMenuInit('%(label)s');
//-->
</script>
</form>
''' % data

        return html

    def editbar(self, d):
        """ Assemble the page edit bar.

        Create html on first call, then return cached html.

        @param d: parameter dictionary
        @rtype: unicode
        @return: iconbar html
        """
        page = d['page']
        if not self.shouldShowEditbar(page):
            return ''

        html = self._cache.get('editbar')
        if html is None:
            # Remove empty items and format as list. The item for showing inline comments
            # is hidden by default. It gets activated through javascript only if inline
            # comments exist on the page.
            items = []
            for item in self.editbarItems(page):
                if item:
                    if 'nbcomment' in item:
                        # hiding the complete list item is cosmetically better than just
                        # hiding the contents (e.g. for sidebar themes).
                        items.append('<li class="toggleCommentsButton" style="display:none;">%s</li>' % item)
                    else:
                        items.append('<li>%s</li>' % item)
            html = u'<ul class="editbar">%s</ul>\n' % ''.join(items)
            self._cache['editbar'] = html

        return html

    def shouldShowEditbar(self, page):
        """ Should we show the editbar?

        Actions should implement this, because only the action knows if
        the edit bar makes sense. Until it goes into actions, we do the
        checking here.

        @param page: current page
        @rtype: bool
        @return: true if editbar should show
        """
        # Show editbar only for existing pages, including deleted pages,
        # that the user may read. If you may not read, you can't edit,
        # so you don't need editbar.
        if (page.exists(includeDeleted=1) and
            self.request.user.may.read(page.page_name)):
            form = self.request.form
            action = self.request.action
            # Do not show editbar on edit but on save/cancel
            return not (action == 'edit' and
                        not form.has_key('button_save') and
                        not form.has_key('button_cancel'))
        return False

    def editbarItems(self, page):
        """ Return list of items to show on the editbar

        This is separate method to make it easy to customize the
        edtibar in sub classes.
        """
        _ = self.request.getText
        editbar_actions = []
        for editbar_item in self.request.cfg.edit_bar:
            if (editbar_item == 'Discussion' and
               (self.request.getPragma('supplementation-page', self.request.cfg.supplementation_page)
                                                   in (True, 1, 'on', '1'))):
                    editbar_actions.append(self.supplementation_page_nameLink(page))
            elif editbar_item == 'Comments':
                # we just use <a> to get same style as other links, but we add some dummy
                # link target to get correct mouseover pointer appearance. return false
                # keeps the browser away from jumping to the link target::
                editbar_actions.append('<a href="#" class="nbcomment" onClick="toggleComments();return false;">%s</a>' % _('Comments'))
            elif editbar_item == 'Edit':
                editbar_actions.append(self.editorLink(page))
            elif editbar_item == 'Info':
                editbar_actions.append(self.infoLink(page))
            elif editbar_item == 'Subscribe':
                editbar_actions.append(self.subscribeLink(page))
            elif editbar_item == 'Quicklink':
                editbar_actions.append(self.quicklinkLink(page))
            elif editbar_item == 'Attachments':
                editbar_actions.append(self.attachmentsLink(page))
            elif editbar_item == 'ActionsMenu':
                editbar_actions.append(self.actionsMenu(page))
        return editbar_actions

    def supplementation_page_nameLink(self, page):
        """Return a link to the discussion page

           If the discussion page doesn't exist and the user
           has no right to create it, show a disabled link.
        """
        _ = self.request.getText
        suppl_name = self.request.cfg.supplementation_page_name
        suppl_name_full = "%s/%s" % (page.page_name, suppl_name)

        test = Page(self.request, suppl_name_full)
        if not test.exists() and not self.request.user.may.write(suppl_name_full):
            return ('<span class="disabled">%s</span>' % _(suppl_name))
        else:
            return page.link_to(self.request, text=_(suppl_name),
                                querystr={'action': 'supplementation'}, css_class='nbsupplementation', rel='nofollow')

    def guiworks(self, page):
        """ Return whether the gui editor / converter can work for that page.

            The GUI editor currently only works for wiki format.
            For simplicity, we also tell it does not work if the admin forces the text editor.
        """
        is_wiki = page.pi['format'] == 'wiki'
        gui_disallowed = self.cfg.editor_force and self.cfg.editor_default == 'text'
        return is_wiki and not gui_disallowed


    def editorLink(self, page):
        """ Return a link to the editor

        If the user can't edit, return a disabled edit link.

        If the user want to show both editors, it will display "Edit
        (Text)", otherwise as "Edit".
        """
        if 'edit' in self.request.cfg.actions_excluded:
            return ""

        if not (page.isWritable() and
                self.request.user.may.write(page.page_name)):
            return self.disabledEdit()

        _ = self.request.getText
        querystr = {'action': 'edit'}

        guiworks = self.guiworks(page)
        if self.showBothEditLinks() and guiworks:
            text = _('Edit (Text)')
            querystr['editor'] = 'text'
            attrs = {'name': 'texteditlink', 'rel': 'nofollow', }
        else:
            text = _('Edit')
            if guiworks:
                # 'textonly' will be upgraded dynamically to 'guipossible' by JS
                querystr['editor'] = 'textonly'
                attrs = {'name': 'editlink', 'rel': 'nofollow', }
            else:
                querystr['editor'] = 'text'
                attrs = {'name': 'texteditlink', 'rel': 'nofollow', }

        return page.link_to(self.request, text=text, querystr=querystr, **attrs)

    def showBothEditLinks(self):
        """ Return True if both edit links should be displayed """
        editor = self.request.user.editor_ui
        if editor == '<default>':
            editor = self.request.cfg.editor_ui
        return editor == 'freechoice'

    def guiEditorScript(self, d):
        """ Return a script that set the gui editor link variables

        The link will be created only when javascript is enabled and
        the browser is compatible with the editor.
        """
        page = d['page']
        if not (page.isWritable() and
                self.request.user.may.write(page.page_name) and
                self.showBothEditLinks() and
                self.guiworks(page)):
            return ''

        _ = self.request.getText
        return """\
<script type="text/javascript">
<!-- // GUI edit link and i18n
var gui_editor_link_href = "%(url)s";
var gui_editor_link_text = "%(text)s";
//-->
</script>
""" % {'url': page.url(self.request, querystr={'action': 'edit', 'editor': 'gui', }),
       'text': _('Edit (GUI)'),
      }

    def disabledEdit(self):
        """ Return a disabled edit link """
        _ = self.request.getText
        return ('<span class="disabled">%s</span>'
                % _('Immutable Page'))

    def infoLink(self, page):
        """ Return link to page information """
        if 'info' in self.request.cfg.actions_excluded:
            return ""

        _ = self.request.getText
        return page.link_to(self.request,
                            text=_('Info'),
                            querystr={'action': 'info'}, css_class='nbinfo', rel='nofollow')

    def subscribeLink(self, page):
        """ Return subscribe/unsubscribe link to valid users

        @rtype: unicode
        @return: subscribe or unsubscribe link
        """
        if not ((self.cfg.mail_enabled or self.cfg.jabber_enabled) and self.request.user.valid):
            return ''

        _ = self.request.getText
        if self.request.user.isSubscribedTo([page.page_name]):
            action, text = 'unsubscribe', _("Unsubscribe")
        else:
            action, text = 'subscribe', _("Subscribe")
        if action in self.request.cfg.actions_excluded:
            return ""
        return page.link_to(self.request, text=text, querystr={'action': action}, css_class='nbsubscribe', rel='nofollow')

    def quicklinkLink(self, page):
        """ Return add/remove quicklink link

        @rtype: unicode
        @return: link to add or remove a quicklink
        """
        if not self.request.user.valid:
            return ''

        _ = self.request.getText
        if self.request.user.isQuickLinkedTo([page.page_name]):
            action, text = 'quickunlink', _("Remove Link")
        else:
            action, text = 'quicklink', _("Add Link")
        if action in self.request.cfg.actions_excluded:
            return ""
        return page.link_to(self.request, text=text, querystr={'action': action}, css_class='nbquicklink', rel='nofollow')

    def attachmentsLink(self, page):
        """ Return link to page attachments """
        if 'AttachFile' in self.request.cfg.actions_excluded:
            return ""

        _ = self.request.getText
        return page.link_to(self.request,
                            text=_('Attachments'),
                            querystr={'action': 'AttachFile'}, css_class='nbattachments', rel='nofollow')

    def startPage(self):
        """ Start page div with page language and direction

        @rtype: unicode
        @return: page div with language and direction attribtues
        """
        return u'<div id="page"%s>\n' % self.content_lang_attr()

    def endPage(self):
        """ End page div

        Add an empty page bottom div to prevent floating elements to
        float out of the page bottom over the footer.
        """
        return '<div id="pagebottom"></div>\n</div>\n'

    # Public functions #####################################################

    def header(self, d, **kw):
        """ Assemble page header

        Default behavior is to start a page div. Sub class and add
        footer items.

        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        return self.startPage()

    editorheader = header

    def footer(self, d, **keywords):
        """ Assemble page footer

        Default behavior is to end page div. Sub class and add
        footer items.

        @param d: parameter dictionary
        @keyword ...:...
        @rtype: string
        @return: page footer html
        """
        return self.endPage()

    # RecentChanges ######################################################

    def recentchanges_entry(self, d):
        """
        Assemble a single recentchanges entry (table row)

        @param d: parameter dictionary
        @rtype: string
        @return: recentchanges entry html
        """
        _ = self.request.getText
        html = []
        html.append('<tr>\n')

        html.append('<td class="rcicon1">%(icon_html)s</td>\n' % d)

        html.append('<td class="rcpagelink">%(pagelink_html)s</td>\n' % d)

        html.append('<td class="rctime">')
        if d['time_html']:
            html.append("%(time_html)s" % d)
        html.append('</td>\n')

        html.append('<td class="rcicon2">%(info_html)s</td>\n' % d)

        html.append('<td class="rceditor">')
        if d['editors']:
            html.append('<br>'.join(d['editors']))
        html.append('</td>\n')

        html.append('<td class="rccomment">')
        if d['comments']:
            if d['changecount'] > 1:
                notfirst = 0
                for comment in d['comments']:
                    html.append('%s<tt>#%02d</tt>&nbsp;%s' % (
                        notfirst and '<br>' or '', comment[0], comment[1]))
                    notfirst = 1
            else:
                comment = d['comments'][0]
                html.append('%s' % comment[1])
        html.append('</td>\n')

        html.append('</tr>\n')

        return ''.join(html)

    def recentchanges_daybreak(self, d):
        """
        Assemble a rc daybreak indication (table row)

        @param d: parameter dictionary
        @rtype: string
        @return: recentchanges daybreak html
        """
        if d['bookmark_link_html']:
            set_bm = '&nbsp; %(bookmark_link_html)s' % d
        else:
            set_bm = ''
        return ('<tr class="rcdaybreak"><td colspan="%d">'
                '<strong>%s</strong>'
                '%s'
                '</td></tr>\n') % (6, d['date'], set_bm)

    def recentchanges_header(self, d):
        """
        Assemble the recentchanges header (intro + open table)

        @param d: parameter dictionary
        @rtype: string
        @return: recentchanges header html
        """
        _ = self.request.getText

        # Should use user interface language and direction
        html = '<div class="recentchanges"%s>\n' % self.ui_lang_attr()
        html += '<div>\n'
        page = d['page']
        if self.shouldUseRSS(page):
            link = [
                u'<div class="rcrss">',
                self.request.formatter.url(1, self.rsshref(page)),
                self.request.formatter.rawHTML(self.make_icon("rss")),
                self.request.formatter.url(0),
                u'</div>',
                ]
            html += ''.join(link)
        html += '<p>'
        # Add day selector
        if d['rc_days']:
            days = []
            for day in d['rc_days']:
                if day == d['rc_max_days']:
                    days.append('<strong>%d</strong>' % day)
                else:
                    days.append(
                        wikiutil.link_tag(self.request,
                            '%s?max_days=%d' % (d['q_page_name'], day),
                            str(day),
                            self.request.formatter, rel='nofollow'))
            days = ' | '.join(days)
            html += (_("Show %s days.") % (days, ))

        if d['rc_update_bookmark']:
            html += " %(rc_update_bookmark)s %(rc_curr_bookmark)s" % d

        html += '</p>\n</div>\n'

        html += '<table>\n'
        return html

    def recentchanges_footer(self, d):
        """
        Assemble the recentchanges footer (close table)

        @param d: parameter dictionary
        @rtype: string
        @return: recentchanges footer html
        """
        _ = self.request.getText
        html = ''
        html += '</table>\n'
        if d['rc_msg']:
            html += "<br>%(rc_msg)s\n" % d
        html += '</div>\n'
        return html

    # Language stuff ####################################################

    def ui_lang_attr(self):
        """Generate language attributes for user interface elements

        User interface elements use the user language (if any), kept in
        request.lang.

        @rtype: string
        @return: lang and dir html attributes
        """
        lang = self.request.lang
        return ' lang="%s" dir="%s"' % (lang, i18n.getDirection(lang))

    def content_lang_attr(self):
        """Generate language attributes for wiki page content

        Page content uses the page language or the wiki default language.

        @rtype: string
        @return: lang and dir html attributes
        """
        lang = self.request.content_lang
        return ' lang="%s" dir="%s"' % (lang, i18n.getDirection(lang))

    def add_msg(self, msg, msg_class=None):
        """ Adds a message to a list which will be used to generate status
        information.

        @param msg: additional message
        @param msg_class: html class for the div of the additional message.
        """
        if not msg_class:
            msg_class = 'dialog'
        if self._send_title_called:
            import traceback
            logging.warning("Calling add_msg() after send_title(): no message can be added.")
            logging.info('\n'.join(['Call stack for add_msg():'] + traceback.format_stack()))

            return
        self._status.append((msg, msg_class))

    # stuff from wikiutil.py
    def send_title(self, text, **keywords):
        """
        Output the page header (and title).

        @param text: the title text
        @keyword page: the page instance that called us - using this is more efficient than using pagename..
        @keyword pagename: 'PageName'
        @keyword print_mode: 1 (or 0)
        @keyword editor_mode: 1 (or 0)
        @keyword media: css media type, defaults to 'screen'
        @keyword allow_doubleclick: 1 (or 0)
        @keyword html_head: additional <head> code
        @keyword body_attr: additional <body> attributes
        @keyword body_onload: additional "onload" JavaScript code
        """
        request = self.request
        _ = request.getText
        rev = request.rev

        if keywords.has_key('page'):
            page = keywords['page']
            pagename = page.page_name
        else:
            pagename = keywords.get('pagename', '')
            page = Page(request, pagename)
        if keywords.get('msg', ''):
            raise DeprecationWarning("Using send_page(msg=) is deprecated! Use theme.add_msg() instead!")
        scriptname = request.script_root

        # get name of system pages
        page_front_page = wikiutil.getFrontPage(request).page_name
        page_help_contents = wikiutil.getLocalizedPage(request, 'HelpContents').page_name
        page_title_index = wikiutil.getLocalizedPage(request, 'TitleIndex').page_name
        page_site_navigation = wikiutil.getLocalizedPage(request, 'SiteNavigation').page_name
        page_word_index = wikiutil.getLocalizedPage(request, 'WordIndex').page_name
        page_help_formatting = wikiutil.getLocalizedPage(request, 'HelpOnFormatting').page_name
        page_find_page = wikiutil.getLocalizedPage(request, 'FindPage').page_name
        home_page = wikiutil.getInterwikiHomePage(request) # sorry theme API change!!! Either None or tuple (wikiname,pagename) now.
        page_parent_page = getattr(page.getParentPage(), 'page_name', None)

        # set content_type, including charset, so web server doesn't touch it:
        request.content_type = "text/html; charset=%s" % (config.charset, )

        # Prepare the HTML <head> element
        user_head = [request.cfg.html_head]

        # include charset information - needed for moin_dump or any other case
        # when reading the html without a web server
        user_head.append('''<meta http-equiv="Content-Type" content="%s;charset=%s">\n''' % (page.output_mimetype, page.output_charset))

        meta_keywords = request.getPragma('keywords')
        meta_desc = request.getPragma('description')
        if meta_keywords:
            user_head.append('<meta name="keywords" content="%s">\n' % wikiutil.escape(meta_keywords, 1))
        if meta_desc:
            user_head.append('<meta name="description" content="%s">\n' % wikiutil.escape(meta_desc, 1))

        #  add meta statement if user has doubleclick on edit turned on or it is default
        if (pagename and keywords.get('allow_doubleclick', 0) and
            not keywords.get('print_mode', 0) and
            request.user.edit_on_doubleclick):
            if request.user.may.write(pagename): # separating this gains speed
                user_head.append('<meta name="edit_on_doubleclick" content="%s">\n' % (request.script_root or '/'))

        # search engine precautions / optimization:
        # if it is an action or edit/search, send query headers (noindex,nofollow):
        if request.query_string:
            user_head.append(request.cfg.html_head_queries)
        elif request.method == 'POST':
            user_head.append(request.cfg.html_head_posts)
        # we don't want to have BadContent stuff indexed:
        elif pagename in ['BadContent', 'LocalBadContent', ]:
            user_head.append(request.cfg.html_head_posts)
        # if it is a special page, index it and follow the links - we do it
        # for the original, English pages as well as for (the possibly
        # modified) frontpage:
        elif pagename in [page_front_page, request.cfg.page_front_page,
                          page_title_index, 'TitleIndex',
                          page_find_page, 'FindPage',
                          page_site_navigation, 'SiteNavigation',
                          'RecentChanges', ]:
            user_head.append(request.cfg.html_head_index)
        # if it is a normal page, index it, but do not follow the links, because
        # there are a lot of illegal links (like actions) or duplicates:
        else:
            user_head.append(request.cfg.html_head_normal)

        if 'pi_refresh' in keywords and keywords['pi_refresh']:
            user_head.append('<meta http-equiv="refresh" content="%d;URL=%s">' % keywords['pi_refresh'])

        # output buffering increases latency but increases throughput as well
        output = []
        # later: <html xmlns=\"http://www.w3.org/1999/xhtml\">
        output.append("""\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
%s
%s
%s
""" % (
            ''.join(user_head),
            self.html_head({
                'page': page,
                'title': text,
                'sitename': request.cfg.html_pagetitle or request.cfg.sitename,
                'print_mode': keywords.get('print_mode', False),
                'media': keywords.get('media', 'screen'),
            }),
            keywords.get('html_head', ''),
        ))

        # Links
        output.append('<link rel="Start" href="%s">\n' % request.href(page_front_page))
        if pagename:
            output.append('<link rel="Alternate" title="%s" href="%s">\n' % (
                    _('Wiki Markup'), request.href(pagename, action='raw')))
            output.append('<link rel="Alternate" media="print" title="%s" href="%s">\n' % (
                    _('Print View'), request.href(pagename, action='print')))

            # !!! currently disabled due to Mozilla link prefetching, see
            # http://www.mozilla.org/projects/netlib/Link_Prefetching_FAQ.html
            #~ all_pages = request.getPageList()
            #~ if all_pages:
            #~     try:
            #~         pos = all_pages.index(pagename)
            #~     except ValueError:
            #~         # this shopuld never happend in theory, but let's be sure
            #~         pass
            #~     else:
            #~         request.write('<link rel="First" href="%s/%s">\n' % (request.script_root, quoteWikinameURL(all_pages[0]))
            #~         if pos > 0:
            #~             request.write('<link rel="Previous" href="%s/%s">\n' % (request.script_root, quoteWikinameURL(all_pages[pos-1])))
            #~         if pos+1 < len(all_pages):
            #~             request.write('<link rel="Next" href="%s/%s">\n' % (request.script_root, quoteWikinameURL(all_pages[pos+1])))
            #~         request.write('<link rel="Last" href="%s/%s">\n' % (request.script_root, quoteWikinameURL(all_pages[-1])))

            if page_parent_page:
                output.append('<link rel="Up" href="%s">\n' % request.href(page_parent_page))

        # write buffer because we call AttachFile
        request.write(''.join(output))
        output = []

        # XXX maybe this should be removed completely. moin emits all attachments as <link rel="Appendix" ...>
        # and it is at least questionable if this fits into the original intent of rel="Appendix".
        if pagename and request.user.may.read(pagename):
            from MoinMoin.action import AttachFile
            AttachFile.send_link_rel(request, pagename)

        output.extend([
            '<link rel="Search" href="%s">\n' % request.href(page_find_page),
            '<link rel="Index" href="%s">\n' % request.href(page_title_index),
            '<link rel="Glossary" href="%s">\n' % request.href(page_word_index),
            '<link rel="Help" href="%s">\n' % request.href(page_help_formatting),
                      ])

        output.append("</head>\n")
        request.write(''.join(output))
        output = []

        # start the <body>
        bodyattr = []
        if keywords.has_key('body_attr'):
            bodyattr.append(' ')
            bodyattr.append(keywords['body_attr'])

        # Set body to the user interface language and direction
        bodyattr.append(' %s' % self.ui_lang_attr())

        body_onload = keywords.get('body_onload', '')
        if body_onload:
            bodyattr.append(''' onload="%s"''' % body_onload)
        output.append('\n<body%s>\n' % ''.join(bodyattr))

        # Output -----------------------------------------------------------

        # If in print mode, start page div and emit the title
        if keywords.get('print_mode', 0):
            d = {
                'title_text': text,
                'page': page,
                'page_name': pagename or '',
                'rev': rev,
            }
            request.themedict = d
            output.append(self.startPage())
            output.append(self.interwiki(d))
            output.append(self.title(d))

        # In standard mode, emit theme.header
        else:
            exists = pagename and page.exists(includeDeleted=True)
            # prepare dict for theme code:
            d = {
                'theme': self.name,
                'script_name': scriptname,
                'title_text': text,
                'logo_string': request.cfg.logo_string,
                'site_name': request.cfg.sitename,
                'page': page,
                'rev': rev,
                'pagesize': pagename and page.size() or 0,
                # exists checked to avoid creation of empty edit-log for non-existing pages
                'last_edit_info': exists and page.lastEditInfo() or '',
                'page_name': pagename or '',
                'page_find_page': page_find_page,
                'page_front_page': page_front_page,
                'home_page': home_page,
                'page_help_contents': page_help_contents,
                'page_help_formatting': page_help_formatting,
                'page_parent_page': page_parent_page,
                'page_title_index': page_title_index,
                'page_word_index': page_word_index,
                'user_name': request.user.name,
                'user_valid': request.user.valid,
                'msg': self._status,
                'trail': keywords.get('trail', None),
                # Discontinued keys, keep for a while for 3rd party theme developers
                'titlesearch': 'use self.searchform(d)',
                'textsearch': 'use self.searchform(d)',
                'navibar': ['use self.navibar(d)'],
                'available_actions': ['use self.request.availableActions(page)'],
            }

            # add quoted versions of pagenames
            newdict = {}
            for key in d:
                if key.startswith('page_'):
                    if not d[key] is None:
                        newdict['q_'+key] = wikiutil.quoteWikinameURL(d[key])
                    else:
                        newdict['q_'+key] = None
            d.update(newdict)
            request.themedict = d

            # now call the theming code to do the rendering
            if keywords.get('editor_mode', 0):
                output.append(self.editorheader(d))
            else:
                output.append(self.header(d))

        # emit it
        request.write(''.join(output))
        output = []
        self._send_title_called = True

    def send_footer(self, pagename, **keywords):
        """
        Output the page footer.

        @param pagename: WikiName of the page
        @keyword print_mode: true, when page is displayed in Print mode
        """
        request = self.request
        d = request.themedict

        # Emit end of page in print mode, or complete footer in standard mode
        if keywords.get('print_mode', 0):
            request.write(self.pageinfo(d['page']))
            request.write(self.endPage())
        else:
            request.write(self.footer(d, **keywords))

    # stuff moved from request.py
    def send_closing_html(self):
        """ generate timing info html and closing html tag,
            everyone calling send_title must call this at the end to close
            the body and html tags.
        """
        request = self.request

        # as this is the last chance to emit some html, we stop the clocks:
        request.clock.stop('run')
        request.clock.stop('total')

        # Close html code
        if request.cfg.show_timings and request.action != 'print':
            request.write('<ul id="timings">\n')
            for t in request.clock.dump():
                request.write('<li>%s</li>\n' % t)
            request.write('</ul>\n')
        #request.write('<!-- auth_method == %s -->' % repr(request.user.auth_method))
        request.write('</body>\n</html>\n\n')

    def sidebar(self, d, **keywords):
        """ Display page called SideBar as an additional element on every page

        @param d: parameter dictionary
        @rtype: string
        @return: sidebar html
        """

        # Check which page to display, return nothing if doesn't exist.
        sidebar = self.request.getPragma('sidebar', u'SideBar')
        page = Page(self.request, sidebar)
        if not page.exists():
            return u""
        # Capture the page's generated HTML in a buffer.
        buffer = StringIO.StringIO()
        self.request.redirect(buffer)
        try:
            page.send_page(content_only=1, content_id="sidebar")
        finally:
            self.request.redirect()
        return u'<div class="sidebar">%s</div>' % buffer.getvalue()


class ThemeNotFound(Exception):
    """ Thrown if the supplied theme could not be found anywhere """

def load_theme(request, theme_name=None):
    """ Load a theme for this request.

    @param request: moin request
    @param theme_name: the name of the theme
    @type theme_name: str
    @rtype: Theme
    @return: a theme initialized for the request
    """
    if theme_name is None or theme_name == '<default>':
        theme_name = request.cfg.theme_default

    try:
        Theme = wikiutil.importPlugin(request.cfg, 'theme', theme_name, 'Theme')
    except wikiutil.PluginMissingError:
        raise ThemeNotFound(theme_name)

    return Theme(request)

def load_theme_fallback(request, theme_name=None):
    """ Try loading a theme, falling back to defaults on error.

    @param request: moin request
    @param theme_name: the name of the theme
    @type theme_name: str
    @rtype: int
    @return: A statuscode for how successful the loading was
             0 - theme was loaded
             1 - fallback to default theme
             2 - serious fallback to builtin theme
    """
    fallback = 0
    try:
        request.theme = load_theme(request, theme_name)
    except ThemeNotFound:
        fallback = 1
        try:
            request.theme = load_theme(request, request.cfg.theme_default)
        except ThemeNotFound:
            fallback = 2
            from MoinMoin.theme.modern import Theme
            request.theme = Theme(request)
