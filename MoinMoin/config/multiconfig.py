# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Multiple configuration handler and Configuration defaults class

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2005-2006 MoinMoin:ThomasWaldmann.
    @license: GNU GPL, see COPYING for details.
"""

import re
import os
import sys
import time

from MoinMoin import config, error, util, wikiutil
import MoinMoin.auth as authmodule
from MoinMoin import session
from MoinMoin.packages import packLine
from MoinMoin.security import AccessControlList

_url_re_cache = None
_farmconfig_mtime = None
_config_cache = {}


def _importConfigModule(name):
    """ Import and return configuration module and its modification time
    
    Handle all errors except ImportError, because missing file is not
    always an error.
    
    @param name: module name
    @rtype: tuple
    @return: module, modification time
    """
    try:
        module = __import__(name, globals(), {})
        mtime = os.path.getmtime(module.__file__)
    except ImportError:
        raise
    except IndentationError, err:
        msg = '''IndentationError: %(err)s

The configuration files are python modules. Therefore, whitespace is
important. Make sure that you use only spaces, no tabs are allowed here!
You have to use four spaces at the beginning of the line mostly.
''' % {
    'err': err,
}
        raise error.ConfigurationError(msg)
    except Exception, err:
        msg = '%s: %s' % (err.__class__.__name__, str(err))
        raise error.ConfigurationError(msg)
    return module, mtime


def _url_re_list():
    """ Return url matching regular expression

    Import wikis list from farmconfig on the first call and compile the
    regexes. Later then return the cached regex list.

    @rtype: list of tuples of (name, compiled re object)
    @return: url to wiki config name matching list
    """
    global _url_re_cache, _farmconfig_mtime
    if _url_re_cache is None:
        try:
            farmconfig, _farmconfig_mtime = _importConfigModule('farmconfig')
        except ImportError:
            # Default to wikiconfig for all urls.
            _farmconfig_mtime = 0
            _url_re_cache = [('wikiconfig', re.compile(r'.')), ] # matches everything
        else:
            try:
                cache = []
                for name, regex in farmconfig.wikis:
                    cache.append((name, re.compile(regex)))
                _url_re_cache = cache
            except AttributeError:
                msg = """
Missing required 'wikis' list in 'farmconfig.py'.

If you run a single wiki you do not need farmconfig.py. Delete it and
use wikiconfig.py.
"""
                raise error.ConfigurationError(msg)
    return _url_re_cache


def _makeConfig(name):
    """ Create and return a config instance 

    Timestamp config with either module mtime or farmconfig mtime. This
    mtime can be used later to invalidate older caches.

    @param name: module name
    @rtype: DefaultConfig sub class instance
    @return: new configuration instance
    """
    global _farmconfig_mtime
    try:
        module, mtime = _importConfigModule(name)
        configClass = getattr(module, 'Config')
        cfg = configClass(name)
        cfg.cfg_mtime = max(mtime, _farmconfig_mtime)
    except ImportError, err:
        msg = '''ImportError: %(err)s

Check that the file is in the same directory as the server script. If
it is not, you must add the path of the directory where the file is
located to the python path in the server script. See the comments at
the top of the server script.

Check that the configuration file name is either "wikiconfig.py" or the
module name specified in the wikis list in farmconfig.py. Note that the
module name does not include the ".py" suffix.
''' % {
    'err': err,
}
        raise error.ConfigurationError(msg)
    except AttributeError, err:
        msg = '''AttributeError: %(err)s

Could not find required "Config" class in "%(name)s.py".

This might happen if you are trying to use a pre 1.3 configuration file, or
made a syntax or spelling error.

Another reason for this could be a name clash. It is not possible to have
config names like e.g. stats.py - because that colides with MoinMoin/stats/ -
have a look into your MoinMoin code directory what other names are NOT
possible.

Please check your configuration file. As an example for correct syntax,
use the wikiconfig.py file from the distribution.
''' % {
    'name': name,
    'err': err,
}
        raise error.ConfigurationError(msg)

    # postprocess configuration
    # 'setuid' special auth method auth method can log out
    cfg.auth_can_logout = ['setuid']
    cfg.auth_login_inputs = []
    found_names = []
    for auth in cfg.auth:
        if not auth.name:
            raise error.ConfigurationError("Auth methods must have a name.")
        if auth.name in found_names:
            raise error.ConfigurationError("Auth method names must be unique.")
        found_names.append(auth.name)
        if auth.logout_possible and auth.name:
            cfg.auth_can_logout.append(auth.name)
        for input in auth.login_inputs:
            if not input in cfg.auth_login_inputs:
                cfg.auth_login_inputs.append(input)
    cfg.auth_have_login = len(cfg.auth_login_inputs) > 0

    return cfg


def _getConfigName(url):
    """ Return config name for url or raise """
    for name, regex in _url_re_list():
        match = regex.match(url)
        if match:
            return name
    raise error.NoConfigMatchedError


def getConfig(url):
    """ Return cached config instance for url or create new one

    If called by many threads in the same time multiple config
    instances might be created. The first created item will be
    returned, using dict.setdefault.

    @param url: the url from request, possibly matching specific wiki
    @rtype: DefaultConfig subclass instance
    @return: config object for specific wiki
    """
    cfgName = _getConfigName(url)
    try:
        cfg = _config_cache[cfgName]
    except KeyError:
        cfg = _makeConfig(cfgName)
        cfg = _config_cache.setdefault(cfgName, cfg)
    return cfg


# This is a way to mark some text for the gettext tools so that they don't
# get orphaned. See http://www.python.org/doc/current/lib/node278.html.
def _(text):
    return text


class CacheClass:
    """ just a container for stuff we cache """
    pass


class DefaultConfig:
    """ default config values """

    # setting DesktopEdition = True gives all local users special powers - ONLY use for MMDE style usage!
    DesktopEdition = False

    # All acl_rights_* lines must use unicode!
    acl_rights_default = u"Trusted:read,write,delete,revert Known:read,write,delete,revert All:read,write"
    acl_rights_before = u""
    acl_rights_after = u""
    acl_rights_valid = ['read', 'write', 'delete', 'revert', 'admin']

    actions_excluded = [] # ['DeletePage', 'AttachFile', 'RenamePage', 'test', ]
    allow_xslt = False
    antispam_master_url = "http://moinmaster.wikiwikiweb.de:8000/?action=xmlrpc2"
    attachments = None # {'dir': path, 'url': url-prefix}
    auth = [authmodule.MoinLogin()]
    # default to http and xmlrpc_applytoken to get old semantics
    # xmlrpc_applytoken shall be removed once that code is changed
    # to have proper session handling and use request.handle_auth()
    trusted_auth_methods = ['xmlrpc_applytoken']
    session_handler = session.DefaultSessionHandler()

    backup_compression = 'gz'
    backup_users = []
    backup_include = []
    backup_exclude = [
        r"(.+\.py(c|o)$)",
        r"%(cache_dir)s",
        r"%(/)spages%(/)s.+%(/)scache%(/)s[^%(/)s]+$" % {'/': os.sep},
        r"%(/)s(edit-lock|event-log|\.DS_Store)$" % {'/': os.sep},
        ]
    backup_storage_dir = '/tmp'
    backup_restore_target_dir = '/tmp'

    bang_meta = True
    caching_formats = ['text_html']
    changed_time_fmt = '%H:%M'

    # chars_{upper,lower,digits,spaces} see MoinMoin/util/chartypes.py

    # if you have gdchart, add something like
    # chart_options = {'width = 720, 'height': 540}
    chart_options = None

    config_check_enabled = False

    cookie_domain = None # use '.domain.tld" for a farm with hosts in that domain
    cookie_path = None   # use '/wikifarm" for a farm with pathes below that path
    cookie_lifetime = 12 # 12 hours from now

    data_dir = './data/'
    data_underlay_dir = './underlay/'

    date_fmt = '%Y-%m-%d'
    datetime_fmt = '%Y-%m-%d %H:%M:%S'

    default_markup = 'wiki'
    docbook_html_dir = r"/usr/share/xml/docbook/stylesheet/nwalsh/html/" # correct for debian sarge

    edit_bar = ['Edit', 'Comments', 'Discussion', 'Info', 'Subscribe', 'Quicklink', 'Attachments', 'ActionsMenu'] 
    editor_default = 'text' # which editor is called when nothing is specified
    editor_ui = 'freechoice' # which editor links are shown on user interface
    editor_force = False
    editor_quickhelp = {# editor markup hints quickhelp 
        'wiki': _("""\
 Emphasis:: [[Verbatim('')]]''italics''[[Verbatim('')]]; [[Verbatim(''')]]'''bold'''[[Verbatim(''')]]; [[Verbatim(''''')]]'''''bold italics'''''[[Verbatim(''''')]]; [[Verbatim('')]]''mixed ''[[Verbatim(''')]]'''''bold'''[[Verbatim(''')]] and italics''[[Verbatim('')]]; [[Verbatim(----)]] horizontal rule.
 Headings:: [[Verbatim(=)]] Title 1 [[Verbatim(=)]]; [[Verbatim(==)]] Title 2 [[Verbatim(==)]]; [[Verbatim(===)]] Title 3 [[Verbatim(===)]];   [[Verbatim(====)]] Title 4 [[Verbatim(====)]]; [[Verbatim(=====)]] Title 5 [[Verbatim(=====)]].
 Lists:: space and one of: * bullets; 1., a., A., i., I. numbered items; 1.#n start numbering at n; space alone indents.
 Links:: [[Verbatim(JoinCapitalizedWords)]]; [[Verbatim(["brackets and double quotes"])]]; url; [url]; [url label].
 Tables:: || cell text |||| cell text spanning 2 columns ||;    no trailing white space allowed after tables or titles.

(!) For more help, see HelpOnEditing or SyntaxReference.
"""),
        'rst': _("""\
Emphasis: <i>*italic*</i> <b>**bold**</b> ``monospace``<br/>
<br/><pre>
Headings: Heading 1  Heading 2  Heading 3
          =========  ---------  ~~~~~~~~~

Horizontal rule: ---- 
Links: TrailingUnderscore_ `multi word with backticks`_ external_ 

.. _external: http://external-site.net/foo/

Lists: * bullets; 1., a. numbered items.
</pre>
<br/>
(!) For more help, see the 
<a href="http://docutils.sourceforge.net/docs/user/rst/quickref.html">
reStructuredText Quick Reference
</a>.
"""),
    }
    edit_locking = 'warn 10' # None, 'warn <timeout mins>', 'lock <timeout mins>'
    edit_ticketing = True
    edit_rows = 20

    hacks = {} # { 'feature1': value1, ... }
               # Configuration for features still in development.
               # For boolean stuff just use config like this:
               #   hacks = { 'feature': True, ...}
               # and in the code use:
               #   if cfg.hacks.get('feature', False): <doit>
               # A non-existing hack key should ever mean False, None, "", [] or {}!

    hosts_deny = []

    html_head = ''
    html_head_queries = '''<meta name="robots" content="noindex,nofollow">\n'''
    html_head_posts   = '''<meta name="robots" content="noindex,nofollow">\n'''
    html_head_index   = '''<meta name="robots" content="index,follow">\n'''
    html_head_normal  = '''<meta name="robots" content="index,nofollow">\n'''
    html_pagetitle = None

    interwiki_preferred = [] # list of wiki names to show at top of interwiki list

    language_default = 'en'
    language_ignore_browser = False # ignore browser settings, use language_default
                                    # or user prefs

    log_reverse_dns_lookups = True  # if we do reverse dns lookups for logging hostnames
                                    # instead of just IPs

    xapian_search = False
    xapian_index_dir = None
    xapian_stemming = True
    xapian_index_history = True
    search_results_per_page = 10

    mail_login = None # or "user pwd" if you need to use SMTP AUTH
    mail_sendmail = None # "/usr/sbin/sendmail -t -i" to not use SMTP, but sendmail
    mail_smarthost = None
    mail_from = None # u'Juergen Wiki <noreply@jhwiki.org>'

    mail_import_subpage_template = u"$from-$date-$subject" # used for mail import
    mail_import_pagename_search = ['subject', 'to', ] # where to look for target pagename (and in which order)
    mail_import_pagename_envelope = u"%s" # use u"+ %s/" to add "+ " and "/" automatically
    mail_import_pagename_regex = r'\["([^"]*)"\]' # how to find/extract the pagename from the subject
    mail_import_wiki_addrs = [] # the e-mail addresses for e-mails that should go into the wiki
    mail_import_secret = ""

    # some dangerous mimetypes (we don't use "content-disposition: inline" for them when a user
    # downloads such attachments, because the browser might execute e.g. Javascript contained
    # in the HTML and steal your moin cookie or do other nasty stuff) 
    mimetypes_xss_protect = [
        'text/html',
        'application/x-shockwave-flash',
        'application/xhtml+xml',
    ]

    mimetypes_embed = [
        'application/x-dvi',
        'application/postscript',
        'application/pdf',
        'application/ogg',
        'application/vnd.visio',
        'image/x-ms-bmp',
        'image/svg+xml',
        'image/tiff',
        'image/x-photoshop',
        'audio/mpeg',
        'audio/midi',
        'audio/x-wav',
        'video/fli',
        'video/mpeg',
        'video/quicktime',
        'video/x-msvideo',
        'chemical/x-pdb',
        'x-world/x-vrml',
    ]


    navi_bar = [u'RecentChanges', u'FindPage', u'HelpContents', ]
    nonexist_qm = False

    page_credits = [
        '<a href="http://moinmoin.wikiwikiweb.de/">MoinMoin Powered</a>',
        '<a href="http://www.python.org/">Python Powered</a>',
        '<a href="http://validator.w3.org/check?uri=referer">Valid HTML 4.01</a>',
        ]
    page_footer1 = ''
    page_footer2 = ''

    page_header1 = ''
    page_header2 = ''

    page_front_page = u'HelpOnLanguages' # this will make people choose a sane config
    page_local_spelling_words = u'LocalSpellingWords'
    page_category_regex = u'^Category[A-Z]'
    page_dict_regex = u'[a-z0-9]Dict$'
    page_group_regex = u'[a-z0-9]Group$'
    page_template_regex = u'[a-z0-9]Template$'

    page_license_enabled = False
    page_license_page = u'WikiLicense'

    # These icons will show in this order in the iconbar, unless they
    # are not relevant, e.g email icon when the wiki is not configured
    # for email.
    page_iconbar = ["edit", "view", "diff", "info", "subscribe", "raw", "print", ]

    # Standard buttons in the iconbar
    page_icons_table = {
        # key           querystr dict, title, icon-key
        'diff':        ({'action': 'diff'}, _("Diffs"), "diff"),
        'info':        ({'action': 'info'}, _("Info"), "info"),
        'edit':        ({'action': 'edit'}, _("Edit"), "edit"),
        'unsubscribe': ({'action': 'subscribe'}, _("UnSubscribe"), "unsubscribe"),
        'subscribe':   ({'action': 'subscribe'}, _("Subscribe"), "subscribe"),
        'raw':         ({'action': 'raw'}, _("Raw"), "raw"),
        'xml':         ({'action': 'show', 'mimetype': 'text/xml'}, _("XML"), "xml"),
        'print':       ({'action': 'print'}, _("Print"), "print"),
        'view':        ({}, _("View"), "view"),
        }

    quicklinks_default = [] # preload user quicklinks with this page list
    refresh = None # (minimum_delay, type), e.g.: (2, 'internal')
    rss_cache = 60 # suggested caching time for RecentChanges RSS, in seconds
    sistersites = [
        #('Self', 'http://localhost:8080/?action=sisterpages'),
        ('EmacsWiki', 'http://www.emacswiki.org/cgi-bin/test?action=sisterpages'),
        ('JspWiki', 'http://www.jspwiki.org/SisterSites.jsp'),
    ] # list of (sistersitename, sisterpagelistfetchurl)
    shared_intermap = None # can be string or list of strings (filenames)
    show_hosts = True
    show_interwiki = False
    show_names = True
    show_section_numbers = 0
    show_timings = False
    show_version = False
    siteid = 'default'
    stylesheets = [] # list of tuples (media, csshref) to insert after theme css, before user css
    subscribed_pages_default = [] # preload user subscribed pages with this page list
    superuser = [] # list of unicode user names that have super powers :)
    supplementation_page = False
    supplementation_page_name = u'Discussion'
    supplementation_page_template = u'DiscussionTemplate'
    surge_action_limits = {# allow max. <count> <action> requests per <dt> secs
        # action: (count, dt)
        'all': (30, 30),
        'show': (30, 60),
        'recall': (5, 60),
        'raw': (20, 40),  # some people use this for css
        'AttachFile': (90, 60),
        'diff': (30, 60),
        'fullsearch': (5, 60),
        'edit': (10, 120),
        'rss_rc': (1, 60),
        'default': (30, 60),
    }
    surge_lockout_time = 3600 # secs you get locked out when you ignore warnings

    theme_default = 'modern'
    theme_force = False

    trail_size = 5
    tz_offset = 0.0 # default time zone offset in hours from UTC

    user_autocreate = False # do we auto-create user profiles
    user_email_unique = True # do we check whether a user's email is unique?

    # a regex of HTTP_USER_AGENTS that should be excluded from logging
    # and receive a FORBIDDEN for anything except viewing a page
    ua_spiders = ('archiver|cfetch|crawler|curl|gigabot|googlebot|holmes|htdig|httrack|httpunit|jeeves|larbin|leech|'
                  'linkbot|linkmap|linkwalk|mercator|mirror|msnbot|neomo|nutbot|omniexplorer|puf|robot|scooter|seekbot|'
                  'sherlock|slurp|sitecheck|spider|teleport|voyager|webreaper|wget')

    # Wiki identity
    sitename = u'Untitled Wiki'

    # url_prefix is DEPRECATED and not used any more by the code.
    # it confused many people by its name and default value of '/wiki' to the
    # wrong conclusion that it is the url of the wiki (the dynamic) stuff,
    # but it was used to address the static stuff (images, css, js).
    # Thus we use the more clear url_prefix_static ['/moin_staticVVV'] setting now.
    # For a limited time, we still look at url_prefix - if it is not None, we
    # copy the value to url_prefix_static to ease transition.
    url_prefix = None

    # includes the moin version number, so we can have a unlimited cache lifetime
    # for the static stuff. if stuff changes on version upgrade, url will change
    # immediately and we have no problem with stale caches.
    url_prefix_static = config.url_prefix_static
    url_prefix_local = None # if None, use same value as url_prefix_static.
                            # must be same site as wiki engine (for e.g. JS permissions)

    # we could prefix actions to be able to exclude them by robots.txt:
    #url_prefix_action = 'action' # no leading or trailing '/'
    url_prefix_action = None # compatiblity

    logo_string = None
    interwikiname = None

    url_mappings = {}

    user_checkbox_fields = [
        ('mailto_author', lambda _: _('Publish my email (not my wiki homepage) in author info')),
        ('edit_on_doubleclick', lambda _: _('Open editor on double click')),
        ('remember_last_visit', lambda _: _('After login, jump to last visited page')),
        ('show_comments', lambda _: _('Show comment sections')),
        ('show_nonexist_qm', lambda _: _('Show question mark for non-existing pagelinks')),
        ('show_page_trail', lambda _: _('Show page trail')),
        ('show_toolbar', lambda _: _('Show icon toolbar')),
        ('show_topbottom', lambda _: _('Show top/bottom links in headings')),
        ('show_fancy_diff', lambda _: _('Show fancy diffs')),
        ('wikiname_add_spaces', lambda _: _('Add spaces to displayed wiki names')),
        ('remember_me', lambda _: _('Remember login information')),
        ('want_trivial', lambda _: _('Subscribe to trivial changes')),

        ('disabled', lambda _: _('Disable this account forever')),
        # if an account is disabled, it may be used for looking up
        # id -> username for page info and recent changes, but it
        # is not usable for the user any more:
    ]

    user_checkbox_defaults = {'mailto_author':       0,
                              'edit_on_doubleclick': 0,
                              'remember_last_visit': 0,
                              'show_comments':       0,
                              'show_nonexist_qm':    nonexist_qm,
                              'show_page_trail':     1,
                              'show_toolbar':        1,
                              'show_topbottom':      0,
                              'show_fancy_diff':     1,
                              'wikiname_add_spaces': 0,
                              'remember_me':         1,
                              'want_trivial':        0,
                             }

    # don't let the user change those
    # user_checkbox_disable = ['disabled', 'want_trivial']
    user_checkbox_disable = []

    # remove those checkboxes:
    #user_checkbox_remove = ['edit_on_doubleclick', 'show_nonexist_qm', 'show_toolbar', 'show_topbottom',
    #                        'show_fancy_diff', 'wikiname_add_spaces', 'remember_me', 'disabled',]
    user_checkbox_remove = []

    user_form_fields = [
        ('name', _('Name'), "text", "36", _("(Use Firstname''''''Lastname)")),
        ('aliasname', _('Alias-Name'), "text", "36", ''),
        ('password', _('Password'), "password", "36", ''),
        ('password2', _('Password repeat'), "password", "36", _('(Only for password change or new account)')),
        ('email', _('Email'), "text", "36", ''),
        ('css_url', _('User CSS URL'), "text", "40", _('(Leave it empty for disabling user CSS)')),
        ('edit_rows', _('Editor size'), "text", "3", ''),
    ]

    user_form_defaults = {# key: default - do NOT remove keys from here!
        'name': '',
        'aliasname': '',
        'password': '',
        'password2': '',
        'email': '',
        'css_url': '',
        'edit_rows': "20",
    }

    # don't let the user change those, but show them:
    #user_form_disable = ['name', 'aliasname', 'email',]
    user_form_disable = []

    # remove those completely:
    #user_form_remove = ['password', 'password2', 'css_url', 'logout', 'create', 'account_sendmail',]
    user_form_remove = []

    # attributes we do NOT save to the userpref file
    user_transient_fields = ['id', 'valid', 'may', 'auth_username', 'password', 'password2', 'auth_method', 'auth_attribs', ]

    user_homewiki = 'Self' # interwiki name for where user homepages are located

    unzip_single_file_size = 2.0 * 1000**2
    unzip_attachments_space = 200.0 * 1000**2
    unzip_attachments_count = 101 # 1 zip file + 100 files contained in it

    xmlrpc_putpage_enabled = False # if False, putpage will write to a test page only
    xmlrpc_putpage_trusted_only = True # if True, you will need to be http auth authenticated

    SecurityPolicy = None

    def __init__(self, siteid):
        """ Init Config instance """
        self.siteid = siteid
        self.cache = CacheClass()

        from MoinMoin.Page import ItemCache
        self.cache.meta = ItemCache('meta')
        self.cache.pagelists = ItemCache('pagelists')

        if self.config_check_enabled:
            self._config_check()

        # define directories
        self.moinmoin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
        data_dir = os.path.normpath(self.data_dir)
        self.data_dir = data_dir
        for dirname in ('user', 'cache', 'plugin'):
            name = dirname + '_dir'
            if not getattr(self, name, None):
                setattr(self, name, os.path.abspath(os.path.join(data_dir, dirname)))

        # Try to decode certain names which allow unicode
        self._decode()

        # After that, pre-compile some regexes
        self.cache.page_category_regex = re.compile(self.page_category_regex, re.UNICODE)
        self.cache.page_dict_regex = re.compile(self.page_dict_regex, re.UNICODE)
        self.cache.page_group_regex = re.compile(self.page_group_regex, re.UNICODE)
        self.cache.page_template_regex = re.compile(self.page_template_regex, re.UNICODE)
        self.cache.ua_spiders = self.ua_spiders and re.compile(self.ua_spiders, re.I)

        self._check_directories()

        if not isinstance(self.superuser, list):
            msg = """The superuser setting in your wiki configuration is not a list
                     (e.g. ['Sample User', 'AnotherUser']).
                     Please change it in your wiki configuration and try again."""
            raise error.ConfigurationError(msg)

        self._loadPluginModule()

        # Preparse user dicts
        self._fillDicts()

        # Normalize values
        self.language_default = self.language_default.lower()

        # Use site name as default name-logo
        if self.logo_string is None:
            self.logo_string = self.sitename

        # Check for needed modules

        # FIXME: maybe we should do this check later, just before a
        # chart is needed, maybe in the chart module, instead doing it
        # for each request. But this require a large refactoring of
        # current code.
        if self.chart_options:
            try:
                import gdchart
            except ImportError:
                self.chart_options = None

        # post process
        # we replace any string placeholders with config values
        # e.g u'%(page_front_page)s' % self
        self.navi_bar = [elem % self for elem in self.navi_bar]
        self.backup_exclude = [elem % self for elem in self.backup_exclude]

        # list to cache xapian searcher objects
        self.xapian_searchers = []

        # check if mail is possible and set flag:
        self.mail_enabled = (self.mail_smarthost is not None or self.mail_sendmail is not None) and self.mail_from

        # Cache variables for the properties below
        self._iwid = self._iwid_full = self._meta_dict = None

        self.cache.acl_rights_before = AccessControlList(self, [self.acl_rights_before])
        self.cache.acl_rights_default = AccessControlList(self, [self.acl_rights_default])
        self.cache.acl_rights_after = AccessControlList(self, [self.acl_rights_after])

        if self.url_prefix is not None: # remove this code when url_prefix setting is removed
            self.url_prefix_static = self.url_prefix

        action_prefix = self.url_prefix_action
        if action_prefix is not None and action_prefix.endswith('/'): # make sure there is no trailing '/'
            self.url_prefix_action = action_prefix[:-1]

        if self.url_prefix_local is None:
            self.url_prefix_local = self.url_prefix_static


    def load_meta_dict(self):
        """ The meta_dict contains meta data about the wiki instance. """
        if getattr(self, "_meta_dict", None) is None:
            self._meta_dict = wikiutil.MetaDict(os.path.join(self.data_dir, 'meta'), self.cache_dir)
        return self._meta_dict
    meta_dict = property(load_meta_dict)

    # lazily load iwid(_full)
    def make_iwid_property(attr):
        def getter(self):
            if getattr(self, attr, None) is None:
                self.load_IWID()
            return getattr(self, attr)
        return property(getter)
    iwid = make_iwid_property("_iwid")
    iwid_full = make_iwid_property("_iwid_full")

    def load_IWID(self):
        """ Loads the InterWikiID of this instance. It is used to identify the instance
            globally.
            The IWID is available as cfg.iwid
            The full IWID containing the interwiki name is available as cfg.iwid_full
            This method is called by the property.
        """

        try:
            iwid = self.meta_dict['IWID']
        except KeyError:
            iwid = util.random_string(16).encode("hex") + "-" + str(int(time.time()))
            self.meta_dict['IWID'] = iwid
            self.meta_dict.sync()

        self._iwid = iwid
        if self.interwikiname is not None:
            self._iwid_full = packLine([iwid, self.interwikiname])
        else:
            self._iwid_full = packLine([iwid])

    def _config_check(self):
        """ Check namespace and warn about unknown names
        
        Warn about names which are not used by DefaultConfig, except
        modules, classes, _private or __magic__ names.

        This check is disabled by default, when enabled, it will show an
        error message with unknown names.
        """
        unknown = ['"%s"' % name for name in dir(self)
                  if not name.startswith('_') and
                  name not in DefaultConfig.__dict__ and
                  not isinstance(getattr(self, name), (type(sys), type(DefaultConfig)))]
        if unknown:
            msg = """
Unknown configuration options: %s.

For more information, visit HelpOnConfiguration. Please check your
configuration for typos before requesting support or reporting a bug.
""" % ', '.join(unknown)
            raise error.ConfigurationError(msg)

    def _decode(self):
        """ Try to decode certain names, ignore unicode values
        
        Try to decode str using utf-8. If the decode fail, raise FatalError. 

        Certain config variables should contain unicode values, and
        should be defined with u'text' syntax. Python decode these if
        the file have a 'coding' line.
        
        This will allow utf-8 users to use simple strings using, without
        using u'string'. Other users will have to use u'string' for
        these names, because we don't know what is the charset of the
        config files.
        """
        charset = 'utf-8'
        message = u'''
"%(name)s" configuration variable is a string, but should be
unicode. Use %(name)s = u"value" syntax for unicode variables.

Also check your "-*- coding -*-" line at the top of your configuration
file. It should match the actual charset of the configuration file.
'''

        decode_names = (
            'sitename', 'logo_string', 'navi_bar', 'page_front_page',
            'page_category_regex', 'page_dict_regex',
            'page_group_regex', 'page_template_regex', 'page_license_page',
            'page_local_spelling_words', 'acl_rights_default',
            'acl_rights_before', 'acl_rights_after', 'mail_from'
            )

        for name in decode_names:
            attr = getattr(self, name, None)
            if attr:
                # Try to decode strings
                if isinstance(attr, str):
                    try:
                        setattr(self, name, unicode(attr, charset))
                    except UnicodeError:
                        raise error.ConfigurationError(message %
                                                       {'name': name})
                # Look into lists and try to decode strings inside them
                elif isinstance(attr, list):
                    for i in xrange(len(attr)):
                        item = attr[i]
                        if isinstance(item, str):
                            try:
                                attr[i] = unicode(item, charset)
                            except UnicodeError:
                                raise error.ConfigurationError(message %
                                                               {'name': name})

    def _check_directories(self):
        """ Make sure directories are accessible

        Both data and underlay should exists and allow read, write and
        execute.
        """
        mode = os.F_OK | os.R_OK | os.W_OK | os.X_OK
        for attr in ('data_dir', 'data_underlay_dir'):
            path = getattr(self, attr)

            # allow an empty underlay path or None
            if attr == 'data_underlay_dir' and not path:
                continue

            path_pages = os.path.join(path, "pages")
            if not (os.path.isdir(path_pages) and os.access(path_pages, mode)):
                msg = '''
%(attr)s "%(path)s" does not exists, or has incorrect ownership or
permissions.

Make sure the directory and the subdirectory pages are owned by the web
server and are readable, writable and executable by the web server user
and group.

It is recommended to use absolute paths and not relative paths. Check
also the spelling of the directory name.
''' % {'attr': attr, 'path': path, }
                raise error.ConfigurationError(msg)

    def _loadPluginModule(self):
        """ import plugin module under configname.plugin

        To be able to import plugin from arbitrary path, we have to load
        the base package once using imp.load_module. Later, we can use
        standard __import__ call to load plugins in this package.

        Since each wiki has unique plugins, we load the plugin package
        under the wiki configuration module, named self.siteid.
        """
        import imp

        name = self.siteid + '.plugin'
        try:
            # Lock other threads while we check and import
            imp.acquire_lock()
            try:
                # If the module is not loaded, try to load it
                if not name in sys.modules:
                    # Find module on disk and try to load - slow!
                    plugin_parent_dir = os.path.abspath(os.path.join(self.plugin_dir, '..'))
                    fp, path, info = imp.find_module('plugin', [plugin_parent_dir])
                    try:
                        # Load the module and set in sys.modules             
                        module = imp.load_module(name, fp, path, info)
                        sys.modules[self.siteid].plugin = module
                    finally:
                        # Make sure fp is closed properly
                        if fp:
                            fp.close()
            finally:
                imp.release_lock()
        except ImportError, err:
            msg = '''
Could not import plugin package "%(path)s/plugin" because of ImportError:
%(err)s.

Make sure your data directory path is correct, check permissions, and
that the data/plugin directory has an __init__.py file.
''' % {
    'path': self.data_dir,
    'err': str(err),
}
            raise error.ConfigurationError(msg)

    def _fillDicts(self):
        """ fill config dicts

        Fills in missing dict keys of derived user config by copying
        them from this base class.
        """
        # user checkbox defaults
        for key, value in DefaultConfig.user_checkbox_defaults.items():
            if key not in self.user_checkbox_defaults:
                self.user_checkbox_defaults[key] = value

    def __getitem__(self, item):
        """ Make it possible to access a config object like a dict """
        return getattr(self, item)

# remove the gettext pseudo function 
del _

