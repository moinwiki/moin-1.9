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
from MoinMoin.auth import MoinAuth
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
    """ Configuration base class with default config values
        (added below)
    """
    # Things that shouldn't be here...
    _subscribable_events = None

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

        # Cache variables for the properties below
        self._iwid = self._iwid_full = self._meta_dict = None

        self.cache.acl_rights_before = AccessControlList(self, [self.acl_rights_before])
        self.cache.acl_rights_default = AccessControlList(self, [self.acl_rights_default])
        self.cache.acl_rights_after = AccessControlList(self, [self.acl_rights_after])

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


def _default_password_checker(request, username, password):
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


class DefaultExpression(object):
    def __init__(self, exprstr):
        self.text = exprstr
        self.value = eval(exprstr)

options_no_group_name = {
  'session': ('Session settings', None, (
    ('session_handler', DefaultExpression('session.DefaultSessionHandler()'),
     "See HelpOnSessions."),
    ('session_id_handler', DefaultExpression('session.MoinCookieSessionIDHandler()'),
     "Only used by the DefaultSessionHandler, see HelpOnSessions."),
    ('cookie_domain', None, None),
    ('cookie_path', None, None),
    ('cookie_lifetime', 12, None),
    ('anonymous_session_lifetime', None,
     'Session lifetime of users who are not logged in.'),
  )),

  'various': ('Various', None, (
    ('DesktopEdition',
     False,
     'True gives all local users special powers - ONLY use for MMDE style usage!'),
    ('SecurityPolicy',
     None,
     None),

    ('actions_excluded',
     ['xmlrpc',  # we do not want wiki admins unknowingly offering xmlrpc service
      'MyPages',  # only works when used with a non-default SecurityPolicy (e.g. autoadmin)
      'CopyPage',  # has questionable behaviour regarding subpages a user can't read, but can copy
     ],
     None),

    ('allow_xslt', False, None),
    ('antispam_master_url', "http://master.moinmo.in/?action=xmlrpc2", None),
    ('auth', DefaultExpression('[MoinAuth()]'), None),
    ('auth_methods_trusted', ['http', 'xmlrpc_applytoken'], None),

    ('bang_meta', True, None),
    ('caching_formats', ['text_html'], None),
    ('changed_time_fmt', '%H:%M', None),

    ('chart_options', None, None),

    ('config_check_enabled', False, None),

    ('data_dir', './data/', None),
    ('data_underlay_dir', './underlay/', None),

    ('date_fmt', '%Y-%m-%d', None),
    ('datetime_fmt', '%Y-%m-%d %H:%M:%S', None),

    ('default_markup', 'wiki', None),
    ('docbook_html_dir', r"/usr/share/xml/docbook/stylesheet/nwalsh/html/", None),

    ('edit_bar', ['Edit', 'Comments', 'Discussion', 'Info', 'Subscribe', 'Quicklink', 'Attachments', 'ActionsMenu'], None),
    ('editor_default', 'text', None),
    ('editor_force', False, None),
    ('editor_ui', 'freechoice', None),
    ('editor_quickhelp', {
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
    }, None),
    ('edit_locking', 'warn 10', None),
    ('edit_ticketing', True, None),
    ('edit_rows', 20, None),

    ('history_count', (100, 200), None),

    ('hosts_deny', [], None),

    ('html_head', '', None),
    ('html_head_queries', '''<meta name="robots" content="noindex,nofollow">\n''', None),
    ('html_head_posts', '''<meta name="robots" content="noindex,nofollow">\n''', None),
    ('html_head_index', '''<meta name="robots" content="index,follow">\n''', None),
    ('html_head_normal', '''<meta name="robots" content="index,nofollow">\n''', None),
    ('html_pagetitle', None, None),

    ('interwikiname', None, None),
    ('interwiki_preferred', [], None),

    ('language_default', 'en', None),
    ('language_ignore_browser', False, None),

    ('logo_string', None, None),

    ('log_reverse_dns_lookups', True, None),
    ('log_timing', False, None),

    # some dangerous mimetypes (we don't use "content-disposition: inline" for them when a user
    # downloads such attachments, because the browser might execute e.g. Javascript contained
    # in the HTML and steal your moin session cookie or do other nasty stuff)
    ('mimetypes_xss_protect',
     [
       'text/html',
       'application/x-shockwave-flash',
       'application/xhtml+xml',
     ], None),

    ('mimetypes_embed',
     [
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
     ], None),


    ('navi_bar', [u'RecentChanges', u'FindPage', u'HelpContents', ], None),

    ('notification_bot_uri', None, None),

    ('page_credits',
     [
       '<a href="http://moinmo.in/" title="This site uses the MoinMoin Wiki software.">MoinMoin Powered</a>',
       '<a href="http://moinmo.in/Python" title="MoinMoin is written in Python.">Python Powered</a>',
       '<a href="http://moinmo.in/GPL" title="MoinMoin is GPL licensed.">GPL licensed</a>',
       '<a href="http://validator.w3.org/check?uri=referer" title="Click here to validate this page.">Valid HTML 4.01</a>',
     ], None),

    ('page_footer1', '', None),
    ('page_footer2', '', None),
    ('page_header1', '', None),
    ('page_header2', '', None),

    ('page_front_page', u'HelpOnLanguages', None),
    ('page_local_spelling_words', u'LocalSpellingWords', None),

    # the following regexes should match the complete name when used in free text
    # the group 'all' shall match all, while the group 'key' shall match the key only
    # e.g. CategoryFoo -> group 'all' ==  CategoryFoo, group 'key' == Foo
    # moin's code will add ^ / $ at beginning / end when needed
    ('page_category_regex', ur'(?P<all>Category(?P<key>\S+))', None),
    ('page_dict_regex', ur'(?P<all>(?P<key>\S+)Dict)', None),
    ('page_group_regex', ur'(?P<all>(?P<key>\S+)Group)', None),
    ('page_template_regex', ur'(?P<all>(?P<key>\S+)Template)', None),

    ('page_license_enabled', False, None),
    ('page_license_page', u'WikiLicense', None),

    # These icons will show in this order in the iconbar, unless they
    # are not relevant, e.g email icon when the wiki is not configured
    # for email.
    ('page_iconbar', ["up", "edit", "view", "diff", "info", "subscribe", "raw", "print", ], None),

    # Standard buttons in the iconbar
    ('page_icons_table',
     {
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
     }, None),



    ('password_checker', DefaultExpression('_default_password_checker'), None),

    ('quicklinks_default', [], None),

    ('refresh', None, None),
    ('rss_cache', 60, None),

    ('search_results_per_page', 25, None),

    ('shared_intermap', None, None),

    ('show_hosts', True, None),
    ('show_interwiki', False, None),
    ('show_names', True, None),
    ('show_section_numbers', 0, None),
    ('show_timings', False, None),
    ('show_version', False, None),

    ('sistersites', [], None),

    ('siteid', 'default', None),
    ('sitename', u'Untitled Wiki', None),

    ('stylesheets', [], None),

    ('subscribed_pages_default', [], None),
    ('email_subscribed_events_default',
     [
        PageChangedEvent.__name__,
        PageRenamedEvent.__name__,
        PageDeletedEvent.__name__,
        PageCopiedEvent.__name__,
        PageRevertedEvent.__name__,
        FileAttachedEvent.__name__,
     ], None),
    ('jabber_subscribed_events_default', [], None),

    ('superuser', [], None),

    ('supplementation_page', False, None),
    ('supplementation_page_name', u'Discussion', None),
    ('supplementation_page_template', u'DiscussionTemplate', None),

    ('surge_action_limits',
     {# allow max. <count> <action> requests per <dt> secs
        # action: (count, dt)
        'all': (30, 30),
        'show': (30, 60),
        'recall': (10, 120),
        'raw': (20, 40),  # some people use this for css
        'AttachFile': (90, 60),
        'diff': (30, 60),
        'fullsearch': (10, 120),
        'edit': (30, 300), # can be lowered after making preview different from edit
        'rss_rc': (1, 60),
        'default': (30, 60),
     }, None),
    ('surge_lockout_time', 3600, None),

    ('textchas', None, None),
    ('textchas_disabled_group', None, None),

    ('theme_default', 'modern', None),
    ('theme_force', False, None),

    ('traceback_show', True, None),
    ('traceback_log_dir', None, None),

    ('trail_size', 5, None),
    ('tz_offset', 0.0, None),

    # a regex of HTTP_USER_AGENTS that should be excluded from logging
    # and receive a FORBIDDEN for anything except viewing a page
    # list must not contain 'java' because of twikidraw wanting to save drawing uses this useragent
    ('ua_spiders',
     ('archiver|cfetch|charlotte|crawler|curl|gigabot|googlebot|heritrix|holmes|htdig|httrack|httpunit|'
      'intelix|jeeves|larbin|leech|libwww-perl|linkbot|linkmap|linkwalk|litefinder|mercator|'
      'microsoft.url.control|mirror| mj12bot|msnbot|msrbot|neomo|nutbot|omniexplorer|puf|robot|scooter|seekbot|'
      'sherlock|slurp|sitecheck|snoopy|spider|teleport|twiceler|voilabot|voyager|webreaper|wget|yeti'),
     None),

    ('unzip_single_file_size', 2.0 * 1000 ** 2, None),
    ('unzip_attachments_space', 200.0 * 1000 ** 2, None),
    ('unzip_attachments_count', 101, None),

    ('url_mappings', {}, None),

    # includes the moin version number, so we can have a unlimited cache lifetime
    # for the static stuff. if stuff changes on version upgrade, url will change
    # immediately and we have no problem with stale caches.
    ('url_prefix_static', config.url_prefix_static, None),
    ('url_prefix_local', None, None),

    # we could prefix actions to be able to exclude them by robots.txt:
    #url_prefix_action', 'action' # no leading or trailing '/'
    ('url_prefix_action', None, None),

    # allow disabling certain userpreferences plugins
    ('userprefs_disabled', [], None),
  )),
}

options = {
    'acl': ('Access control lists', None, (
      ('hierarchic', False, 'True to use hierarchical ACLs'),
      ('rights_default', u"Trusted:read,write,delete,revert Known:read,write,delete,revert All:read,write", None),
      ('rights_before', u"", None),
      ('rights_after', u"", None),
      ('rights_valid', ['read', 'write', 'delete', 'revert', 'admin'], None),
    )),

    'xapian': ('Xapian search', None, (
      ('search', False, None),
      ('index_dir', None, None),
      ('stemming', False, None),
      ('index_history', False, None),
    )),

    'user': ('Users / User settings', None, (
      ('autocreate', False, None),
      ('email_unique', True, None),
      ('jid_unique', True, None),

      ('homewiki', 'Self', None),

      ('checkbox_fields',
       [
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
       ],
       None),

      ('checkbox_defaults',
       {
        'mailto_author':       0,
        'edit_on_doubleclick': 0,
        'remember_last_visit': 0,
        'show_comments':       0,
        'show_nonexist_qm':    False,
        'show_page_trail':     1,
        'show_toolbar':        1,
        'show_topbottom':      0,
        'show_fancy_diff':     1,
        'wikiname_add_spaces': 0,
        'remember_me':         1,
       },
       None),

      ('checkbox_disable', [], None),

      ('checkbox_remove', [], None),

      ('form_fields',
       [
        ('name', _('Name'), "text", "36", _("(Use FirstnameLastname)")),
        ('aliasname', _('Alias-Name'), "text", "36", ''),
        ('email', _('Email'), "text", "36", ''),
        ('jid', _('Jabber ID'), "text", "36", ''),
        ('css_url', _('User CSS URL'), "text", "40", _('(Leave it empty for disabling user CSS)')),
        ('edit_rows', _('Editor size'), "text", "3", ''),
       ],
       None),

      ('form_defaults',
       { # key: default - do NOT remove keys from here!
        'name': '',
        'aliasname': '',
        'password': '',
        'password2': '',
        'email': '',
        'jid': '',
        'css_url': '',
        'edit_rows': "20",
       },
       None),

      ('form_disable', [], None),

      ('form_remove', [], None),

      ('transient_fields',
       ['id', 'valid', 'may', 'auth_username', 'password', 'password2', 'auth_method', 'auth_attribs', ],
       None),
    )),

    'backup': ('Backup', None, (
      ('compression', 'gz', None),
      ('users', [], None),
      ('include', [], None),
      ('exclude',
       [
        r"(.+\.py(c|o)$)",
        r"%(cache_dir)s",
        r"%(/)spages%(/)s.+%(/)scache%(/)s[^%(/)s]+$" % {'/': os.sep},
        r"%(/)s(edit-lock|event-log|\.DS_Store)$" % {'/': os.sep},
       ],
       None),
      ('storage_dir', '/tmp', None),
      ('restore_target_dir', '/tmp', None),
    )),

    'openid_server': ('OpenID Server',
        'These settings control the built-in OpenID Identity Provider (server).',
    (
      ('enabled', False, None),
      ('restricted_users_group', None, None),
      ('enable_user', False, None),
    )),

    'mail': ('Mail settings',
        'These settings control outgoing and incoming email from and to the wiki.',
    (
      ('from', None, None),
      ('login', None, None),
      ('smarthost', None, None),
      ('sendmail', None, None),

      ('import_secret', "", None),
      ('import_subpage_template', u"$from-$date-$subject", None),
      ('import_pagename_search', ['subject', 'to', ], None),
      ('import_pagename_envelope', u"%s", None),
      ('import_pagename_regex', r'\[\[([^\]]*)\]\]', None),
      ('import_wiki_addrs', [], None),
    )),
}

def _add_options_to_defconfig(opts, addgroup=True):
    for groupname in opts:
        group_short, group_doc, group_opts = opts[groupname]
        for name, default, doc in group_opts:
            if addgroup:
                name = groupname + '_' + name
            if isinstance(default, DefaultExpression):
                default = default.value
            setattr(DefaultConfig, name, default)

_add_options_to_defconfig(options)
_add_options_to_defconfig(options_no_group_name, False)

# remove the gettext pseudo function
del _
