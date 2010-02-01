# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Multiple configuration handler and Configuration defaults class

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2005-2008 MoinMoin:ThomasWaldmann.
    @license: GNU GPL, see COPYING for details.
"""

import re
import os
import sys
import time

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, error, util, wikiutil
import MoinMoin.auth as authmodule
import MoinMoin.events as events
from MoinMoin.events import PageChangedEvent, PageRenamedEvent
from MoinMoin.events import PageDeletedEvent, PageCopiedEvent
from MoinMoin.events import PageRevertedEvent, FileAttachedEvent
from MoinMoin import session
from MoinMoin.packages import packLine
from MoinMoin.security import AccessControlList
from MoinMoin.support.python_compatibility import set

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
        logging.exception('Your source code / config file is not correctly indented!')
        msg = '''IndentationError: %(err)s

The configuration files are python modules. Therefore, whitespace is
important. Make sure that you use only spaces, no tabs are allowed here!
You have to use four spaces at the beginning of the line mostly.
''' % {
    'err': err,
}
        raise error.ConfigurationError(msg)
    except Exception, err:
        logging.exception('An exception happened.')
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
        except ImportError, err:
            if 'farmconfig' in str(err):
                # we failed importing farmconfig
                logging.debug("could not import farmconfig, mapping all URLs to wikiconfig")
                _farmconfig_mtime = 0
                _url_re_cache = [('wikiconfig', re.compile(r'.')), ] # matches everything
            else:
                # maybe there was a failing import statement inside farmconfig
                raise
        else:
            logging.info("using farm config: %s" % os.path.abspath(farmconfig.__file__))
            try:
                cache = []
                for name, regex in farmconfig.wikis:
                    cache.append((name, re.compile(regex)))
                _url_re_cache = cache
            except AttributeError:
                logging.error("required 'wikis' list missing in farmconfig")
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
        logging.info("using wiki config: %s" % os.path.abspath(module.__file__))
    except ImportError, err:
        logging.exception('Could not import.')
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
        logging.exception('An exception occured.')
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


class DefaultConfig(object):
    """ default config values

        When adding new config attributes, PLEASE use a name with the TOPIC as prefix,
        so it will sort naturally. E.g. use "actions_excluded", not "excluded_actions".

        Also, please keep it (roughly) sorted (except if you have good reasons to group otherwise).
    """

    DesktopEdition = False # True gives all local users special powers - ONLY use for MMDE style usage!

    SecurityPolicy = None

    acl_hierarchic = False # True to use hierarchical ACLs
    # All acl_rights_* lines must use unicode!
    acl_rights_default = u"Trusted:read,write,delete,revert Known:read,write,delete,revert All:read,write"
    acl_rights_before = u""
    acl_rights_after = u""
    acl_rights_valid = ['read', 'write', 'delete', 'revert', 'admin']

    actions_excluded = ['xmlrpc',  # we do not want wiki admins unknowingly offering xmlrpc service
                        'MyPages',  # only works when used with a non-default SecurityPolicy (e.g. autoadmin)
                        'CopyPage',  # has questionable behaviour regarding subpages a user can't read, but can copy
                       ]
    allow_xslt = False
    antispam_master_url = "http://master.moinmo.in/?action=xmlrpc2"

    auth = [authmodule.MoinAuth()]
    # default to http and xmlrpc_applytoken to get old semantics
    # xmlrpc_applytoken shall be removed once that code is changed
    # to have proper session handling and use request.handle_auth()
    auth_methods_trusted = ['http', 'xmlrpc_applytoken']

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
    cookie_secure = None # a secure cookie is not transmitted over unsecure connection
                         # None = auto-enable secure cookie for https
                         # True = ever use secure cookie
                         # False = never use secure cookie

    data_dir = './data/'
    data_underlay_dir = './underlay/'

    date_fmt = '%Y-%m-%d'
    datetime_fmt = '%Y-%m-%d %H:%M:%S'

    default_markup = 'wiki'
    docbook_html_dir = r"/usr/share/xml/docbook/stylesheet/nwalsh/html/" # correct for debian sarge

    edit_bar = ['Edit', 'Comments', 'Discussion', 'Info', 'Subscribe', 'Quicklink', 'Attachments', 'ActionsMenu']
    editor_default = 'text' # which editor is called when nothing is specified
    editor_force = False # force using the default editor
    editor_ui = 'freechoice' # which editor links are shown on user interface
    editor_quickhelp = {
        # editor markup hints quickhelp
        # MUST be in wiki markup, even if the help is not for the wiki parser!
        'wiki': _(u"""\
 Emphasis:: <<Verbatim('')>>''italics''<<Verbatim('')>>; <<Verbatim(''')>>'''bold'''<<Verbatim(''')>>; <<Verbatim(''''')>>'''''bold italics'''''<<Verbatim(''''')>>; <<Verbatim('')>>''mixed ''<<Verbatim(''')>>'''''bold'''<<Verbatim(''')>> and italics''<<Verbatim('')>>; <<Verbatim(----)>> horizontal rule.
 Headings:: = Title 1 =; == Title 2 ==; === Title 3 ===; ==== Title 4 ====; ===== Title 5 =====.
 Lists:: space and one of: * bullets; 1., a., A., i., I. numbered items; 1.#n start numbering at n; space alone indents.
 Links:: <<Verbatim(JoinCapitalizedWords)>>; <<Verbatim([[target|linktext]])>>.
 Tables:: || cell text |||| cell text spanning 2 columns ||;    no trailing white space allowed after tables or titles.

(!) For more help, see HelpOnEditing or SyntaxReference.
"""),
        'rst': _("""\
{{{
Emphasis: *italic* **bold** ``monospace``

Headings: Heading 1  Heading 2  Heading 3
          =========  ---------  ~~~~~~~~~

Horizontal rule: ----

Links: TrailingUnderscore_ `multi word with backticks`_ external_

.. _external: http://external-site.example.org/foo/

Lists: * bullets; 1., a. numbered items.
}}}
(!) For more help, see the
[[http://docutils.sourceforge.net/docs/user/rst/quickref.html|reStructuredText Quick Reference]].
"""),
        'creole': _(u"""\
 Emphasis:: <<Verbatim(//)>>''italics''<<Verbatim(//)>>; <<Verbatim(**)>>'''bold'''<<Verbatim(**)>>; <<Verbatim(**//)>>'''''bold italics'''''<<Verbatim(//**)>>; <<Verbatim(//)>>''mixed ''<<Verbatim(**)>>'''''bold'''<<Verbatim(**)>> and italics''<<Verbatim(//)>>;
 Horizontal Rule:: <<Verbatim(----)>>
 Force Linebreak:: <<Verbatim(\\\\)>>
 Headings:: = Title 1 =; == Title 2 ==; === Title 3 ===; ==== Title 4 ====; ===== Title 5 =====.
 Lists:: * bullets; ** sub-bullets; # numbered items; ## numbered sub items.
 Links:: <<Verbatim([[target]])>>; <<Verbatim([[target|linktext]])>>.
 Tables:: |= header text | cell text | more cell text |;

(!) For more help, see HelpOnEditing or HelpOnCreoleSyntax.
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

    history_count = (100, 200) # (default_revisions_shown, max_revisions_shown)

    hosts_deny = []

    html_head = ''
    html_head_queries = '''<meta name="robots" content="noindex,nofollow">\n'''
    html_head_posts   = '''<meta name="robots" content="noindex,nofollow">\n'''
    html_head_index   = '''<meta name="robots" content="index,follow">\n'''
    html_head_normal  = '''<meta name="robots" content="index,nofollow">\n'''
    html_pagetitle = None

    interwikiname = None # our own interwikiname. choose wisely and never change!
    interwiki_preferred = [] # list of wiki names to show at top of interwiki list

    language_default = 'en'
    language_ignore_browser = False # ignore browser settings, use language_default
                                    # or user prefs

    logo_string = None # can be either just some text or a piece of html shown as "logo"

    log_reverse_dns_lookups = True  # if we do reverse dns lookups for logging hostnames
                                    # instead of just IPs
    log_timing = False # log infos about timing of actions, good to analyze load conditions

    mail_from = None # u'Juergen Wiki <noreply@jhwiki.org>'
    mail_login = None # "user pwd" if you need to use SMTP AUTH when using your mail server
    mail_smarthost = None # your SMTP mail server
    mail_sendmail = None # "/usr/sbin/sendmail -t -i" to not use SMTP, but sendmail

    mail_import_secret = "" # a shared secret also known to the mail importer xmlrpc script
    mail_import_subpage_template = u"$from-$date-$subject" # used for mail import
    mail_import_pagename_search = ['subject', 'to', ] # where to look for target pagename (and in which order)
    mail_import_pagename_envelope = u"%s" # use u"+ %s/" to add "+ " and "/" automatically
    mail_import_pagename_regex = r'\[\[([^\]]*)\]\]' # how to find/extract the pagename from the subject
    mail_import_wiki_addrs = [] # the e-mail addresses for e-mails that should go into the wiki

    # some dangerous mimetypes (we don't use "content-disposition: inline" for them when a user
    # downloads such attachments, because the browser might execute e.g. Javascript contained
    # in the HTML and steal your moin session cookie or do other nasty stuff)
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

    notification_bot_uri = None # uri of the jabber bot

    # OpenID server support
    openid_server_enabled = False
    openid_server_restricted_users_group = None
    openid_server_enable_user = False

    page_credits = [
        # Feel free to add other credits, but PLEASE do NOT change or remove
        # the following links - you help us by keeping them "as is":
        '<a href="http://moinmo.in/" title="This site uses the MoinMoin Wiki software.">MoinMoin Powered</a>',
        '<a href="http://moinmo.in/Python" title="MoinMoin is written in Python.">Python Powered</a>',

        # Optional credits:
        # if you think it can be maybe misunderstood as applying to content or topic of your wiki,
        # feel free to remove this one:
        '<a href="http://moinmo.in/GPL" title="MoinMoin is GPL licensed.">GPL licensed</a>',

        # if you don't need/want to check the html output, feel free to remove this one:
        '<a href="http://validator.w3.org/check?uri=referer" title="Click here to validate this page.">Valid HTML 4.01</a>',
        ]

    # you can put some pieces of html at specific places into the theme output:
    page_footer1 = ''
    page_footer2 = ''
    page_header1 = ''
    page_header2 = ''

    page_front_page = u'HelpOnLanguages' # this will make people choose a sane config
    page_local_spelling_words = u'LocalSpellingWords'

    # the following regexes should match the complete name when used in free text
    # the group 'all' shall match all, while the group 'key' shall match the key only
    # e.g. CategoryFoo -> group 'all' ==  CategoryFoo, group 'key' == Foo
    # moin's code will add ^ / $ at beginning / end when needed
    page_category_regex =  ur'(?P<all>Category(?P<key>(?!Template)\S+))'
    page_dict_regex = ur'(?P<all>(?P<key>\S+)Dict)'
    page_group_regex = ur'(?P<all>(?P<key>\S+)Group)'
    page_template_regex = ur'(?P<all>(?P<key>\S+)Template)'

    page_license_enabled = False
    page_license_page = u'WikiLicense'

    # These icons will show in this order in the iconbar, unless they
    # are not relevant, e.g email icon when the wiki is not configured
    # for email.
    page_iconbar = ["up", "edit", "view", "diff", "info", "subscribe", "raw", "print", ]

    # Standard buttons in the iconbar
    page_icons_table = {
        # key           pagekey, querystr dict, title, icon-key
        'diff':        ('page', {'action': 'diff'}, _("Diffs"), "diff"),
        'info':        ('page', {'action': 'info'}, _("Info"), "info"),
        'edit':        ('page', {'action': 'edit'}, _("Edit"), "edit"),
        'unsubscribe': ('page', {'action': 'unsubscribe'}, _("UnSubscribe"), "unsubscribe"),
        'subscribe':   ('page', {'action': 'subscribe'}, _("Subscribe"), "subscribe"),
        'raw':         ('page', {'action': 'raw'}, _("Raw"), "raw"),
        'xml':         ('page', {'action': 'show', 'mimetype': 'text/xml'}, _("XML"), "xml"),
        'print':       ('page', {'action': 'print'}, _("Print"), "print"),
        'view':        ('page', {}, _("View"), "view"),
        'up':          ('page_parent_page', {}, _("Up"), "up"),
        }


    def password_checker(username, password):
        """ Check if a password is secure enough.
            We use a built-in check to get rid of the worst passwords.

            We do NOT use cracklib / python-crack here any more because it is
            not thread-safe (we experienced segmentation faults when using it).

            If you don't want to check passwords, use password_checker = None.

            @return: None if there is no problem with the password,
                     some string with an error msg, if the password is problematic.
        """

        try:
            # in any case, do a very simple built-in check to avoid the worst passwords
            if len(password) < 6:
                raise ValueError("Password too short.")
            if len(set(password)) < 4:
                raise ValueError("Password has not enough different characters.")

            username_lower = username.lower()
            password_lower = password.lower()
            if username in password or password in username or \
               username_lower in password_lower or password_lower in username_lower:
                raise ValueError("Password too easy (containment).")

            keyboards = (ur"`1234567890-=qwertyuiop[]\asdfghjkl;'zxcvbnm,./", # US kbd
                         ur"^1234567890ß´qwertzuiopü+asdfghjklöä#yxcvbnm,.-", # german kbd
                        ) # add more keyboards!
            for kbd in keyboards:
                rev_kbd = kbd[::-1]
                if password in kbd or password in rev_kbd or \
                   password_lower in kbd or password_lower in rev_kbd:
                    raise ValueError("Password too easy (kbd sequence)")
            return None
        except ValueError, err:
            return str(err)

    password_checker = staticmethod(password_checker)

    quicklinks_default = [] # preload user quicklinks with this page list

    refresh = None # (minimum_delay, type), e.g.: (2, 'internal')
    rss_cache = 60 # suggested caching time for RecentChanges RSS, in seconds

    search_results_per_page = 25

    session_handler = session.DefaultSessionHandler()
    session_id_handler = session.MoinCookieSessionIDHandler()

    secrets = None  # if wiki admin does not set it, will get calculated from some cfg values

    shared_intermap = None # can be string or list of strings (filenames)

    show_hosts = True # show hostnames on RecentChanges / info/history action
    show_interwiki = False # show our interwiki name (usually in front of the page name)
    show_names = True # show editor names on RecentChanges / info/history action
    show_section_numbers = 0 # enumerate sections (headlines) by default?
    show_timings = False # show some timing stats (usually in the footer)
    show_version = False # show moin version info / (C) (depends on theme)

    sistersites = [
        #('Self', 'http://localhost:8080/?action=sisterpages'),
        #('EmacsWiki', 'http://www.emacswiki.org/cgi-bin/test?action=sisterpages'),
        #('JspWiki', 'http://www.jspwiki.org/SisterSites.jsp'),
    ] # list of (sistersitename, sisterpagelistfetchurl)

    siteid = 'default'
    sitename = u'Untitled Wiki' # Wiki identity

    stylesheets = [] # list of tuples (media, csshref) to insert after theme css, before user css

    _subscribable_events = None # A list of event types that user can subscribe to
    subscribed_pages_default = [] # preload user subscribed pages with this page list
    email_subscribed_events_default = [
        PageChangedEvent.__name__,
        PageRenamedEvent.__name__,
        PageDeletedEvent.__name__,
        PageCopiedEvent.__name__,
        PageRevertedEvent.__name__,
        FileAttachedEvent.__name__,
    ]
    jabber_subscribed_events_default = []

    superuser = [] # list of unicode user names that have super powers :)

    supplementation_page = False # use supplementation pages (show a link in the theme)?
    supplementation_page_name = u'Discussion' # name of suppl. subpage
    supplementation_page_template = u'DiscussionTemplate' # name of template used to create suppl. pages

    surge_action_limits = {# allow max. <count> <action> requests per <dt> secs
        # action: (count, dt)
        'all': (30, 30), # all requests (except cache/AttachFile action) count for this limit
        'default': (30, 60), # default limit for actions without a specific limit
        'show': (30, 60),
        'recall': (10, 120),
        'raw': (20, 40),  # some people use this for css
        'diff': (30, 60),
        'fullsearch': (10, 120),
        'edit': (30, 300), # can be lowered after making preview different from edit
        'rss_rc': (1, 60),
        # The following actions are often used for images - to avoid pages with lots of images
        # (like photo galleries) triggering surge protection, we assign rather high limits:
        'AttachFile': (90, 60),
        'cache': (600, 30), # cache action is very cheap/efficient
    }
    surge_lockout_time = 3600 # secs you get locked out when you ignore warnings

    textchas = None # a data structure with site-specific questions/answers, see HelpOnTextChas
    textchas_disabled_group = None # e.g. u'NoTextChasGroup' if you are a member of this group, you don't get textchas

    theme_default = 'modern'
    theme_force = False

    traceback_show = True # if True, tracebacks are displayed in the web browser
    traceback_log_dir = None # if set to a directory path, tracebacks are written to files there

    trail_size = 5 # number of recently visited pagenames shown in the trail display
    tz_offset = 0.0 # default time zone offset in hours from UTC

    # a regex of HTTP_USER_AGENTS that should be excluded from logging
    # and receive a FORBIDDEN for anything except viewing a page
    # list must not contain 'java' because of twikidraw wanting to save drawing uses this useragent
    ua_spiders = ('archiver|cfetch|charlotte|crawler|curl|gigabot|googlebot|heritrix|holmes|htdig|httrack|httpunit|'
                  'intelix|jeeves|larbin|leech|libwww-perl|linkbot|linkmap|linkwalk|litefinder|mercator|'
                  'microsoft.url.control|mirror| mj12bot|msnbot|msrbot|neomo|nutbot|omniexplorer|puf|robot|scooter|seekbot|'
                  'sherlock|slurp|sitecheck|snoopy|spider|teleport|twiceler|voilabot|voyager|webreaper|wget|yeti')

    unzip_single_file_size = 2.0 * 1000 ** 2
    unzip_attachments_space = 200.0 * 1000 ** 2
    unzip_attachments_count = 101 # 1 zip file + 100 files contained in it

    url_mappings = {}

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

    # allow disabling certain userpreferences plugins
    userprefs_disabled = []

    user_autocreate = False # do we auto-create user profiles
    user_email_unique = True # do we check whether a user's email is unique?
    user_jid_unique = True # do we check whether a user's email is unique?

    user_homewiki = u'Self' # interwiki name for where user homepages are located

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
                             }

    # don't let the user change those
    # user_checkbox_disable = ['disabled']
    user_checkbox_disable = []

    # remove those checkboxes:
    #user_checkbox_remove = ['edit_on_doubleclick', 'show_nonexist_qm', 'show_toolbar', 'show_topbottom',
    #                        'show_fancy_diff', 'wikiname_add_spaces', 'remember_me', 'disabled',]
    user_checkbox_remove = []

    user_form_fields = [
        ('name', _('Name'), "text", "36", _("(Use FirstnameLastname)")),
        ('aliasname', _('Alias-Name'), "text", "36", ''),
        ('email', _('Email'), "text", "36", ''),
        ('jid', _('Jabber ID'), "text", "36", ''),
        ('css_url', _('User CSS URL'), "text", "40", _('(Leave it empty for disabling user CSS)')),
        ('edit_rows', _('Editor size'), "text", "3", ''),
    ]

    user_form_defaults = {# key: default - do NOT remove keys from here!
        'name': '',
        'aliasname': '',
        'password': '',
        'password2': '',
        'email': '',
        'jid': '',
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

    xapian_search = False
    xapian_index_dir = None
    xapian_stemming = False
    xapian_index_history = False

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

        # the ..._regexact versions only match if nothing is left (exact match)
        self.cache.page_category_regexact = re.compile(u'^%s$' % self.page_category_regex, re.UNICODE)
        self.cache.page_dict_regexact = re.compile(u'^%s$' % self.page_dict_regex, re.UNICODE)
        self.cache.page_group_regexact = re.compile(u'^%s$' % self.page_group_regex, re.UNICODE)
        self.cache.page_template_regexact = re.compile(u'^%s$' % self.page_template_regex, re.UNICODE)

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

        # internal dict for plugin `modules' lists
        self._site_plugin_lists = {}

        # we replace any string placeholders with config values
        # e.g u'%(page_front_page)s' % self
        self.navi_bar = [elem % self for elem in self.navi_bar]
        self.backup_exclude = [elem % self for elem in self.backup_exclude]

        # check if python-xapian is installed
        if self.xapian_search:
            try:
                import xapian
            except ImportError, err:
                self.xapian_search = False
                logging.error("xapian_search was auto-disabled because python-xapian is not installed [%s]." % str(err))

        # list to cache xapian searcher objects
        self.xapian_searchers = []

        # check if mail is possible and set flag:
        self.mail_enabled = (self.mail_smarthost is not None or self.mail_sendmail is not None) and self.mail_from

        # check if jabber bot is available and set flag:
        self.jabber_enabled = self.notification_bot_uri is not None

        # if we are to use the jabber bot, instantiate a server object for future use
        if self.jabber_enabled:

            errmsg = "You must set a (long) secret string to send notifications!"
            try:
                if not self.secret:
                    raise error.ConfigurationError(errmsg)
            except AttributeError, err:
                raise error.ConfigurationError(errmsg)

            from xmlrpclib import Server
            self.notification_server = Server(self.notification_bot_uri, )

        if self.secrets is None:  # Note: this is 'secrets' (with s at the end), not 'secret' (as above)
                                  # This stuff is already cleaned up in 1.8 repo...
            self.secrets = self.calc_secrets()

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


    def calc_secrets(self):
        """ make up some 'secret' using some config values """
        varnames = ['data_dir', 'data_underlay_dir', 'language_default',
                    'mail_smarthost', 'mail_from', 'page_front_page',
                    'theme_default', 'sitename', 'logo_string',
                    'interwikiname', 'user_homewiki', 'acl_rights_before', ]
        secret = ''
        for varname in varnames:
            var = getattr(self, varname, None)
            if isinstance(var, (str, unicode)):
                secret += repr(var)
        return secret

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

    # lazily load a list of events a user can subscribe to
    def make_subscribable_events_prop():
        def getter(self):
            if getattr(self, "_subscribable_events", None) is None:
                self._subscribable_events = events.get_subscribable_events()
            return getattr(self, "_subscribable_events")

        def setter(self, new_events):
            self._subscribable_events = new_events

        return property(getter, setter)
    subscribable_events = make_subscribable_events_prop()

    # lazily create a list of event handlers
    def make_event_handlers_prop():
        def getter(self):
            if getattr(self, "_event_handlers", None) is None:
                self._event_handlers = events.get_handlers(self)
            return getattr(self, "_event_handlers")

        def setter(self, new_handlers):
            self._event_handlers = new_handlers

        return property(getter, setter)
    event_handlers = make_event_handlers_prop()

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
            'sitename', 'interwikiname', 'user_homewiki', 'logo_string', 'navi_bar',
            'page_front_page', 'page_category_regex', 'page_dict_regex',
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
%(attr)s "%(path)s" does not exist, or has incorrect ownership or
permissions.

Make sure the directory and the subdirectory "pages" are owned by the web
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

