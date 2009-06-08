# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RequestBase Implementation

    @copyright: 2001-2003 Juergen Hermann <jh@web.de>,
                2003-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

# Support for remote IP address detection when using (reverse) proxy (or even proxies).
# If you exactly KNOW which (reverse) proxies you can trust, put them into the list
# below, so we can determine the "outside" IP as your trusted proxies see it.

proxies_trusted = [] # trust noone!
#proxies_trusted = ['127.0.0.1', ] # can be a list of multiple IPs

from MoinMoin import log
logging = log.getLogger(__name__)

def find_remote_addr(addrs):
    """ Find the last remote IP address before it hits our reverse proxies.
        The LAST address in the <addrs> list is the remote IP as detected by the server
        (not taken from some x-forwarded-for header).
        The FIRST address in the <addrs> list might be the client's IP - if noone cheats
        and everyone supports x-f-f header.

        See http://bob.pythonmac.org/archives/2005/09/23/apache-x-forwarded-for-caveat/

        For debug loglevel, we log all <addrs>.

        TODO: refactor request code to first do some basic IP init, then load configuration,
        TODO: then do proxy processing.
        TODO: add wikiconfig configurability for proxies_trusted
        TODO: later, make it possible to put multipe remote IP addrs into edit-log
    """
    logging.debug("request.find_remote_addr: addrs == %r" % addrs)
    if proxies_trusted:
        result = [addr for addr in addrs if addr not in proxies_trusted]
        if result:
            return result[-1] # last IP before it hit our trusted (reverse) proxies
    return addrs[-1] # this is a safe remote_addr, not taken from x-f-f header


import os, re, time, sys, cgi, StringIO
import Cookie
import traceback

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil, user, caching, error
from MoinMoin.config import multiconfig
from MoinMoin.support.python_compatibility import set
from MoinMoin.util import IsWin9x
from MoinMoin.util.clock import Clock
from MoinMoin import auth
from urllib import quote, quote_plus

# umask setting --------------------------------------------------------
def set_umask(new_mask=0777^config.umask):
    """ Set the OS umask value (and ignore potential failures on OSes where
        this is not supported).
        Default: the bitwise inverted value of config.umask
    """
    try:
        old_mask = os.umask(new_mask)
    except:
        # maybe we are on win32?
        pass

# We do this at least once per Python process, when request is imported.
# If other software parts (like twistd's daemonize() function) set an
# unwanted umask, we have to call this again to set the correct one:
set_umask()

# Exceptions -----------------------------------------------------------

class MoinMoinFinish(Exception):
    """ Raised to jump directly to end of run() function, where finish is called """


class HeadersAlreadySentException(Exception):
    """ Is raised if the headers were already sent when emit_http_headers is called."""


class RemoteClosedConnection(Exception):
    """ Remote end closed connection during request """

# Utilities

def cgiMetaVariable(header, scheme='http'):
    """ Return CGI meta variable for header name

    e.g 'User-Agent' -> 'HTTP_USER_AGENT'
    See http://www.faqs.org/rfcs/rfc3875.html section 4.1.18
    """
    var = '%s_%s' % (scheme, header)
    return var.upper().replace('-', '_')


# Request Base ----------------------------------------------------------

class RequestBase(object):
    """ A collection for all data associated with ONE request. """

    # Defaults (used by sub classes)
    http_accept_language = 'en'
    server_name = 'localhost'
    server_port = '80'

    # Extra headers we support. Both standalone and twisted store
    # headers as lowercase.
    moin_location = 'x-moin-location'
    proxy_host = 'x-forwarded-host' # original host: header as seen by the proxy (e.g. wiki.example.org)
    proxy_xff = 'x-forwarded-for' # list of original remote_addrs as seen by the proxies (e.g. <clientip>,<proxy1>,<proxy2>,...)

    def __init__(self, properties={}, given_config=None):

        # twistd's daemonize() overrides our umask, so we reset it here every
        # request. we do it for all request types to avoid similar problems.
        set_umask()

        self._finishers = []

        self._auth_redirected = False

        # Decode values collected by sub classes
        self.path_info = self.decodePagename(self.path_info)

        self.failed = 0
        self._available_actions = None
        self._known_actions = None

        # Pages meta data that we collect in one request
        self.pages = {}

        self.sent_headers = None
        self.user_headers = []
        self.cacheable = 0 # may this output get cached by http proxies/caches?
        self.http_caching_disabled = 0 # see disableHttpCaching()
        self.page = None
        self._dicts = None

        # session handling. users cannot rely on a session being
        # created, but we should always set request.session
        self.session = {}

        # setuid handling requires an attribute in the request
        # that stores the real user
        self._setuid_real_user = None

        # Check for dumb proxy requests
        # TODO relying on request_uri will not work on all servers, especially
        # not on external non-Apache servers
        self.forbidden = False
        if self.request_uri.startswith('http://'):
            self.makeForbidden403()

        # Init
        else:
            self.writestack = []
            self.clock = Clock()
            self.clock.start('total')
            self.clock.start('base__init__')
            # order is important here!
            self.__dict__.update(properties)
            try:
                self._load_multi_cfg(given_config)
            except error.NoConfigMatchedError:
                self.makeForbidden(404, 'No wiki configuration matching the URL found!\r\n')
                return

            self.isSpiderAgent = self.check_spider()

            # Set decode charsets.  Input from the user is always in
            # config.charset, which is the page charsets. Except
            # path_info, which may use utf-8, and handled by decodePagename.
            self.decode_charsets = [config.charset]

            if self.query_string.startswith('action=xmlrpc'):
                self.args = {}
                self.form = {}
                self.action = 'xmlrpc'
                self.rev = None
            else:
                try:
                    self.args = self.form = self.setup_args()
                except UnicodeError:
                    self.makeForbidden(403, "The input you sent could not be understood.")
                    return
                self.action = self.form.get('action', ['show'])[0]
                try:
                    self.rev = int(self.form['rev'][0])
                except:
                    self.rev = None

            from MoinMoin.Page import RootPage
            self.rootpage = RootPage(self)

            from MoinMoin.logfile import editlog
            self.editlog = editlog.EditLog(self)

            from MoinMoin import i18n
            self.i18n = i18n
            i18n.i18n_init(self)

            # authentication might require translated forms, so
            # have a try at guessing the language from the browser
            lang = i18n.requestLanguage(self, try_user=False)
            self.getText = lambda text, i18n=self.i18n, request=self, lang=lang, **kw: i18n.getText(text, request, lang, **kw)

            # session handler start, auth
            self.parse_cookie()
            user_obj = self.cfg.session_handler.start(self, self.cfg.session_id_handler)
            shfinisher = lambda request: self.cfg.session_handler.finish(request, request.user,
                                                                         self.cfg.session_id_handler)
            self.add_finisher(shfinisher)
            # set self.user even if _handle_auth_form raises an Exception
            self.user = None
            self.user = self._handle_auth_form(user_obj)
            del user_obj
            self.cfg.session_handler.after_auth(self, self.cfg.session_id_handler, self.user)
            if not self.user:
                self.user = user.User(self, auth_method='request:invalid')

            # setuid handling, check isSuperUser() because the user
            # might have lost the permission between requests
            if 'setuid' in self.session and self.user.isSuperUser():
                self._setuid_real_user = self.user
                uid = self.session['setuid']
                self.user = user.User(self, uid, auth_method='setuid')
                # set valid to True so superusers can even switch
                # to disable accounts
                self.user.valid = True

            if self.action != 'xmlrpc':
                if not self.forbidden and self.isForbidden():
                    self.makeForbidden403()
                if not self.forbidden and self.surge_protect():
                    self.makeUnavailable503()

            self.pragma = {}
            self.mode_getpagelinks = 0 # is > 0 as long as we are in a getPageLinks call
            self.parsePageLinks_running = {} # avoid infinite recursion by remembering what we are already running

            self.lang = i18n.requestLanguage(self)
            # Language for content. Page content should use the wiki default lang,
            # but generated content like search results should use the user language.
            self.content_lang = self.cfg.language_default
            self.getText = lambda text, i18n=self.i18n, request=self, lang=self.lang, **kv: i18n.getText(text, request, lang, **kv)

            self.reset()

            from MoinMoin.formatter.text_html import Formatter
            self.html_formatter = Formatter(self)
            self.formatter = self.html_formatter

            self.clock.stop('base__init__')

    def surge_protect(self, kick_him=False):
        """ check if someone requesting too much from us,
            if kick_him is True, we unconditionally blacklist the current user/ip
        """
        limits = self.cfg.surge_action_limits
        if not limits:
            return False

        if self.remote_addr.startswith('127.'): # localnet
            return False

        validuser = self.user.valid
        current_id = validuser and self.user.name or self.remote_addr
        current_action = self.action

        default_limit = limits.get('default', (30, 60))

        now = int(time.time())
        surgedict = {}
        surge_detected = False

        try:
            # if we have common farm users, we could also use scope='farm':
            cache = caching.CacheEntry(self, 'surgeprotect', 'surge-log', scope='wiki', use_encode=True)
            if cache.exists():
                data = cache.content()
                data = data.split("\n")
                for line in data:
                    try:
                        id, t, action, surge_indicator = line.split("\t")
                        t = int(t)
                        maxnum, dt = limits.get(action, default_limit)
                        if t >= now - dt:
                            events = surgedict.setdefault(id, {})
                            timestamps = events.setdefault(action, [])
                            timestamps.append((t, surge_indicator))
                    except StandardError:
                        pass

            maxnum, dt = limits.get(current_action, default_limit)
            events = surgedict.setdefault(current_id, {})
            timestamps = events.setdefault(current_action, [])
            surge_detected = len(timestamps) > maxnum

            surge_indicator = surge_detected and "!" or ""
            timestamps.append((now, surge_indicator))
            if surge_detected:
                if len(timestamps) < maxnum * 2:
                    timestamps.append((now + self.cfg.surge_lockout_time, surge_indicator)) # continue like that and get locked out

            if current_action not in ('cache', 'AttachFile', ): # don't add cache/AttachFile accesses to all or picture galleries will trigger SP
                current_action = 'all' # put a total limit on user's requests
                maxnum, dt = limits.get(current_action, default_limit)
                events = surgedict.setdefault(current_id, {})
                timestamps = events.setdefault(current_action, [])

                if kick_him: # ban this guy, NOW
                    timestamps.extend([(now + self.cfg.surge_lockout_time, "!")] * (2 * maxnum))

                surge_detected = surge_detected or len(timestamps) > maxnum

                surge_indicator = surge_detected and "!" or ""
                timestamps.append((now, surge_indicator))
                if surge_detected:
                    if len(timestamps) < maxnum * 2:
                        timestamps.append((now + self.cfg.surge_lockout_time, surge_indicator)) # continue like that and get locked out

            data = []
            for id, events in surgedict.items():
                for action, timestamps in events.items():
                    for t, surge_indicator in timestamps:
                        data.append("%s\t%d\t%s\t%s" % (id, t, action, surge_indicator))
            data = "\n".join(data)
            cache.update(data)
        except StandardError:
            pass

        if surge_detected and validuser and self.user.auth_method in self.cfg.auth_methods_trusted:
            logging.info("Trusted user %s would have triggered surge protection if not trusted." % self.user.name)
            return False  # do not subject trusted users to surge protection

        return surge_detected

    def getDicts(self):
        """ Lazy initialize the dicts on the first access """
        if self._dicts is None:
            from MoinMoin import wikidicts
            dicts = wikidicts.GroupDict(self)
            dicts.load_dicts()
            self._dicts = dicts
        return self._dicts

    def delDicts(self):
        """ Delete the dicts, used by some tests """
        del self._dicts
        self._dicts = None

    dicts = property(getDicts, None, delDicts)

    def _load_multi_cfg(self, given_config=None):
        # protect against calling multiple times
        if not hasattr(self, 'cfg'):
            if given_config is None:
                self.clock.start('load_multi_cfg')
                self.cfg = multiconfig.getConfig(self.url)
                self.clock.stop('load_multi_cfg')
            else:
                self.cfg = given_config('MoinMoin._tests.wikiconfig') # used for tests' TestConfig

    def setAcceptedCharsets(self, accept_charset):
        """ Set accepted_charsets by parsing accept-charset header

        Set self.accepted_charsets to an ordered list based on http_accept_charset.

        Reference: http://www.w3.org/Protocols/rfc2616/rfc2616.txt

        TODO: currently no code use this value.

        @param accept_charset: accept-charset header
        """
        charsets = []
        if accept_charset:
            accept_charset = accept_charset.lower()
            # Add iso-8859-1 if needed
            if (not '*' in accept_charset and
                'iso-8859-1' not in accept_charset):
                accept_charset += ',iso-8859-1'

            # Make a list, sorted by quality value, using Schwartzian Transform
            # Create list of tuples (value, name) , sort, extract names
            for item in accept_charset.split(','):
                if ';' in item:
                    name, qval = item.split(';')
                    qval = 1.0 - float(qval.split('=')[1])
                else:
                    name, qval = item, 0
                charsets.append((qval, name))
            charsets.sort()
            # Remove *, its not clear what we should do with it later
            charsets = [name for qval, name in charsets if name != '*']

        self.accepted_charsets = charsets

    def _setup_vars_from_std_env(self, env):
        """ Set common request variables from CGI environment

        Parse a standard CGI environment as created by common web servers.
        Reference: http://www.faqs.org/rfcs/rfc3875.html

        @param env: dict like object containing cgi meta variables
        """
        # Values we can just copy
        self.env = env
        self.http_accept_language = env.get('HTTP_ACCEPT_LANGUAGE', self.http_accept_language)
        self.server_name = env.get('SERVER_NAME', self.server_name)
        self.server_port = env.get('SERVER_PORT', self.server_port)
        self.saved_cookie = env.get('HTTP_COOKIE', '')
        self.script_name = env.get('SCRIPT_NAME', '')
        self.path_info = env.get('PATH_INFO', '')
        self.query_string = env.get('QUERY_STRING', '')
        self.request_method = env.get('REQUEST_METHOD', None)
        self.remote_addr = env.get('REMOTE_ADDR', '')
        self.http_user_agent = env.get('HTTP_USER_AGENT', '')
        try:
            self.content_length = int(env.get('CONTENT_LENGTH'))
        except (TypeError, ValueError):
            self.content_length = None
        self.if_modified_since = env.get('If-modified-since') or env.get(cgiMetaVariable('If-modified-since'))
        self.if_none_match = env.get('If-none-match') or env.get(cgiMetaVariable('If-none-match'))

        # REQUEST_URI is not part of CGI spec, but an addition of Apache.
        self.request_uri = env.get('REQUEST_URI', '')

        # Values that need more work
        self.setHttpReferer(env.get('HTTP_REFERER'))
        self.setIsSSL(env)
        self.setHost(env.get('HTTP_HOST'))
        self.fixURI(env)

        self.setURL(env)
        #self.debugEnvironment(env)

    def setHttpReferer(self, referer):
        """ Set http_referer, making sure its ascii

        IE might send non-ascii value.
        """
        value = ''
        if referer:
            value = unicode(referer, 'ascii', 'replace')
            value = value.encode('ascii', 'replace')
        self.http_referer = value

    def setIsSSL(self, env):
        """ Set is_ssl

        @param env: dict like object containing cgi meta variables
        """
        self.is_ssl = bool(env.get('SSL_PROTOCOL') or
                           env.get('SSL_PROTOCOL_VERSION') or
                           env.get('HTTPS', 'off').lower() in ('on', '1') or
                           env.get('wsgi.url_scheme') == 'https')

    def setHost(self, host=None):
        """ Set http_host

        Create from server name and port if missing. Previous code
        default to localhost.
        """
        if not host:
            port = ''
            standardPort = ('80', '443')[self.is_ssl]
            if self.server_port != standardPort:
                port = ':' + self.server_port
            host = self.server_name + port
        self.http_host = host

    def fixURI(self, env):
        """ Fix problems with script_name and path_info

        Handle the strange charset semantics on Windows and other non
        posix systems. path_info is transformed into the system code
        page by the web server. Additionally, paths containing dots let
        most webservers choke.

        Broken environment variables in different environments:
                path_info script_name
        Apache1     X          X      PI does not contain dots
        Apache2     X          X      PI is not encoded correctly
        IIS         X          X      path_info include script_name
        Other       ?          -      ? := Possible and even RFC-compatible.
                                      - := Hopefully not.

        @param env: dict like object containing cgi meta variables
        """
        # Fix the script_name when using Apache on Windows.
        server_software = env.get('SERVER_SOFTWARE', '')
        if os.name == 'nt' and 'Apache/' in server_software:
            # Removes elements ending in '.' from the path.
            self.script_name = '/'.join([x for x in self.script_name.split('/')
                                         if not x.endswith('.')])

        # Fix path_info
        if os.name != 'posix' and self.request_uri != '':
            # Try to recreate path_info from request_uri.
            import urlparse
            scriptAndPath = urlparse.urlparse(self.request_uri)[2]
            path = scriptAndPath.replace(self.script_name, '', 1)
            self.path_info = wikiutil.url_unquote(path, want_unicode=False)
        elif os.name == 'nt':
            # Recode path_info to utf-8
            path = wikiutil.decodeWindowsPath(self.path_info)
            self.path_info = path.encode("utf-8")

            # Fix bug in IIS/4.0 when path_info contain script_name
            if self.path_info.startswith(self.script_name):
                self.path_info = self.path_info[len(self.script_name):]

    def setURL(self, env):
        """ Set url, used to locate wiki config

        This is the place to manipulate url parts as needed.

        @param env: dict like object containing cgi meta variables or http headers.
        """
        # proxy support
        self.rewriteRemoteAddr(env)
        self.rewriteHost(env)

        self.rewriteURI(env)

        if not self.request_uri:
            self.request_uri = self.makeURI()
        self.url = self.http_host + self.request_uri

    def rewriteHost(self, env):
        """ Rewrite http_host transparently

        Get the proxy host using 'X-Forwarded-Host' header, added by
        Apache 2 and other proxy software.

        TODO: Will not work for Apache 1 or others that don't add this header.

        TODO: If we want to add an option to disable this feature it
        should be in the server script, because the config is not
        loaded at this point, and must be loaded after url is set.

        @param env: dict like object containing cgi meta variables or http headers.
        """
        proxy_host = (env.get(self.proxy_host) or
                      env.get(cgiMetaVariable(self.proxy_host)))
        if proxy_host:
            self.http_host = proxy_host

    def rewriteRemoteAddr(self, env):
        """ Rewrite remote_addr transparently

        Get the proxy remote addr using 'X-Forwarded-For' header, added by
        Apache 2 and other proxy software.

        TODO: Will not work for Apache 1 or others that don't add this header.

        TODO: If we want to add an option to disable this feature it
        should be in the server script, because the config is not
        loaded at this point, and must be loaded after url is set.

        @param env: dict like object containing cgi meta variables or http headers.
        """
        xff = (env.get(self.proxy_xff) or
               env.get(cgiMetaVariable(self.proxy_xff)))
        if xff:
            xff = [addr.strip() for addr in xff.split(',')]
            xff.append(self.remote_addr)
            self.remote_addr = find_remote_addr(xff)

    def rewriteURI(self, env):
        """ Rewrite request_uri, script_name and path_info transparently

        Useful when running mod python or when running behind a proxy,
        e.g run on localhost:8000/ and serve as example.com/wiki/.

        Uses private 'X-Moin-Location' header to set the script name.
        This allow setting the script name when using Apache 2
        <location> directive::

            <Location /my/wiki/>
                RequestHeader set X-Moin-Location /my/wiki/
            </location>

        TODO: does not work for Apache 1 and others that do not allow
        setting custom headers per request.

        @param env: dict like object containing cgi meta variables or http headers.
        """
        location = (env.get(self.moin_location) or
                    env.get(cgiMetaVariable(self.moin_location)))
        if location is None:
            return

        scriptAndPath = self.script_name + self.path_info
        location = location.rstrip('/')
        self.script_name = location

        # This may happen when using mod_python
        if scriptAndPath.startswith(location):
            self.path_info = scriptAndPath[len(location):]

        # Recreate the URI from the modified parts
        if self.request_uri:
            self.request_uri = self.makeURI()

    def makeURI(self):
        """ Return uri created from uri parts """
        uri = self.script_name + wikiutil.url_quote(self.path_info)
        if self.query_string:
            uri += '?' + self.query_string
        return uri

    def splitURI(self, uri):
        """ Return path and query splited from uri

        Just like CGI environment, the path is unquoted, the query is not.
        """
        if '?' in uri:
            path, query = uri.split('?', 1)
        else:
            path, query = uri, ''
        return wikiutil.url_unquote(path, want_unicode=False), query

    def _handle_auth_form(self, user_obj):
        username = self.form.get('name', [None])[0]
        password = self.form.get('password', [None])[0]
        oid = self.form.get('openid_identifier', [None])[0]
        login = 'login' in self.form
        logout = 'logout' in self.form
        stage = self.form.get('stage', [None])[0]
        return self.handle_auth(user_obj, attended=True, username=username,
                                password=password, login=login, logout=logout,
                                stage=stage, openid_identifier=oid)

    def handle_auth(self, user_obj, attended=False, **kw):
        username = kw.get('username')
        password = kw.get('password')
        oid = kw.get('openid_identifier')
        login = kw.get('login')
        logout = kw.get('logout')
        stage = kw.get('stage')
        extra = {
            'cookie': self.cookie,
        }
        if login:
            extra['attended'] = attended
            extra['username'] = username
            extra['password'] = password
            extra['openid_identifier'] = oid
            if stage:
                extra['multistage'] = True
        login_msgs = []
        self._login_multistage = None

        if logout and 'setuid' in self.session:
            del self.session['setuid']
            return user_obj

        for authmethod in self.cfg.auth:
            if logout:
                user_obj, cont = authmethod.logout(self, user_obj, **extra)
            elif login:
                if stage and authmethod.name != stage:
                    continue
                ret = authmethod.login(self, user_obj, **extra)
                user_obj = ret.user_obj
                cont = ret.continue_flag
                if stage:
                    stage = None
                    del extra['multistage']
                if ret.multistage:
                    self._login_multistage = ret.multistage
                    self._login_multistage_name = authmethod.name
                    return user_obj
                if ret.redirect_to:
                    nextstage = auth.get_multistage_continuation_url(self, authmethod.name)
                    url = ret.redirect_to
                    url = url.replace('%return_form', quote_plus(nextstage))
                    url = url.replace('%return', quote(nextstage))
                    self._auth_redirected = True
                    self.http_redirect(url)
                    return user_obj
                msg = ret.message
                if msg and not msg in login_msgs:
                    login_msgs.append(msg)
            else:
                user_obj, cont = authmethod.request(self, user_obj, **extra)
            if not cont:
                break

        self._login_messages = login_msgs
        return user_obj

    def handle_jid_auth(self, jid):
        return user.get_by_jabber_id(self, jid)

    def parse_cookie(self):
        try:
            self.cookie = Cookie.SimpleCookie(self.saved_cookie)
        except Cookie.CookieError:
            self.cookie = None

    def reset(self):
        """ Reset request state.

        Called after saving a page, before serving the updated
        page. Solves some practical problems with request state
        modified during saving.

        """
        # This is the content language and has nothing to do with
        # The user interface language. The content language can change
        # during the rendering of a page by lang macros
        self.current_lang = self.cfg.language_default

        # caches unique ids
        self.init_unique_ids()

        if hasattr(self, "_fmt_hd_counters"):
            del self._fmt_hd_counters

    def loadTheme(self, theme_name):
        """ Load the Theme to use for this request.

        @param theme_name: the name of the theme
        @type theme_name: str
        @rtype: int
        @return: success code
                 0 on success
                 1 if user theme could not be loaded,
                 2 if a hard fallback to modern theme was required.
        """
        fallback = 0
        if theme_name == "<default>":
            theme_name = self.cfg.theme_default

        try:
            Theme = wikiutil.importPlugin(self.cfg, 'theme', theme_name, 'Theme')
        except wikiutil.PluginMissingError:
            fallback = 1
            try:
                Theme = wikiutil.importPlugin(self.cfg, 'theme', self.cfg.theme_default, 'Theme')
            except wikiutil.PluginMissingError:
                fallback = 2
                from MoinMoin.theme.modern import Theme

        self.theme = Theme(self)
        return fallback

    def setContentLanguage(self, lang):
        """ Set the content language, used for the content div

        Actions that generate content in the user language, like search,
        should set the content direction to the user language before they
        call send_title!
        """
        self.content_lang = lang
        self.current_lang = lang

    def getPragma(self, key, defval=None):
        """ Query a pragma value (#pragma processing instruction)

            Keys are not case-sensitive.
        """
        return self.pragma.get(key.lower(), defval)

    def setPragma(self, key, value):
        """ Set a pragma value (#pragma processing instruction)

            Keys are not case-sensitive.
        """
        self.pragma[key.lower()] = value

    def getPathinfo(self):
        """ Return the remaining part of the URL. """
        return self.path_info

    def getScriptname(self):
        """ Return the scriptname part of the URL ('/path/to/my.cgi'). """
        if self.script_name == '/':
            return ''
        return self.script_name

    def getKnownActions(self):
        """ Create a dict of avaiable actions

        Return cached version if avaiable.

        @rtype: dict
        @return: dict of all known actions
        """
        try:
            self.cfg.cache.known_actions # check
        except AttributeError:
            from MoinMoin import action
            self.cfg.cache.known_actions = set(action.getNames(self.cfg))

        # Return a copy, so clients will not change the set.
        return self.cfg.cache.known_actions.copy()

    def getAvailableActions(self, page):
        """ Get list of avaiable actions for this request

        The dict does not contain actions that starts with lower case.
        Themes use this dict to display the actions to the user.

        @param page: current page, Page object
        @rtype: dict
        @return: dict of avaiable actions
        """
        if self._available_actions is None:
            # some actions might make sense for non-existing pages, so we just
            # require read access here. Can be later refined to some action
            # specific check:
            if not self.user.may.read(page.page_name):
                return []

            # Filter non ui actions (starts with lower case letter)
            actions = self.getKnownActions()
            actions = [action for action in actions if not action[0].islower()]

            # Filter wiki excluded actions
            actions = [action for action in actions if not action in self.cfg.actions_excluded]

            # Filter actions by page type, acl and user state
            excluded = []
            if ((page.isUnderlayPage() and not page.isStandardPage()) or
                not self.user.may.write(page.page_name) or
                not self.user.may.delete(page.page_name)):
                # Prevent modification of underlay only pages, or pages
                # the user can't write and can't delete
                excluded = [u'RenamePage', u'DeletePage', ] # AttachFile must NOT be here!
            actions = [action for action in actions if not action in excluded]

            self._available_actions = set(actions)

        # Return a copy, so clients will not change the dict.
        return self._available_actions.copy()

    def redirectedOutput(self, function, *args, **kw):
        """ Redirect output during function, return redirected output """
        buf = StringIO.StringIO()
        self.redirect(buf)
        try:
            function(*args, **kw)
        finally:
            self.redirect()
        text = buf.getvalue()
        buf.close()
        return text

    def redirect(self, file=None):
        """ Redirect output to file, or restore saved output """
        if file:
            self.writestack.append(self.write)
            self.write = file.write
        else:
            self.write = self.writestack.pop()

    def log(self, msg):
        """ DEPRECATED - Log msg to logging framework
            Please call logging.info(...) directly!
        """
        msg = msg.strip()
        # Encode unicode msg
        if isinstance(msg, unicode):
            msg = msg.encode(config.charset)
        logging.info(msg)

    def timing_log(self, start, action):
        """ Log to timing log (for performance analysis) """
        indicator = ''
        if start:
            total = "vvv"
        else:
            self.clock.stop('total') # make sure it is stopped
            total_secs = self.clock.timings['total']
            # we add some stuff that is easy to grep when searching for peformance problems:
            if total_secs > 50:
                indicator += '!4!'
            elif total_secs > 20:
                indicator += '!3!'
            elif total_secs > 10:
                indicator += '!2!'
            elif total_secs > 2:
                indicator += '!1!'
            total = self.clock.value('total')
            # use + for existing pages, - for non-existing pages
            if self.page is not None:
                indicator += self.page.exists() and '+' or '-'
            if self.isSpiderAgent:
                indicator += "B"

        pid = os.getpid()
        msg = 'Timing %5d %-6s %4s %-10s %s' % (pid, total, indicator, action, self.url)
        logging.info(msg)

    def send_file(self, fileobj, bufsize=8192, do_flush=False):
        """ Send a file to the output stream.

        @param fileobj: a file-like object (supporting read, close)
        @param bufsize: size of chunks to read/write
        @param do_flush: call flush after writing?
        """
        while True:
            buf = fileobj.read(bufsize)
            if not buf:
                break
            self.write(buf)
            if do_flush:
                self.flush()

    def write(self, *data):
        """ Write to output stream. """
        raise NotImplementedError

    def encode(self, data):
        """ encode data (can be both unicode strings and strings),
            preparing for a single write()
        """
        wd = []
        for d in data:
            try:
                if isinstance(d, unicode):
                    # if we are REALLY sure, we can use "strict"
                    d = d.encode(config.charset, 'replace')
                elif d is None:
                    continue
                wd.append(d)
            except UnicodeError:
                logging.error("Unicode error on: %s" % repr(d))
        return ''.join(wd)

    def decodePagename(self, name):
        """ Decode path, possibly using non ascii characters

        Does not change the name, only decode to Unicode.

        First split the path to pages, then decode each one. This enables
        us to decode one page using config.charset and another using
        utf-8. This situation happens when you try to add to a name of
        an existing page.

        See http://www.w3.org/TR/REC-html40/appendix/notes.html#h-B.2.1

        @param name: page name, string
        @rtype: unicode
        @return decoded page name
        """
        # Split to pages and decode each one
        pages = name.split('/')
        decoded = []
        for page in pages:
            # Recode from utf-8 into config charset. If the path
            # contains user typed parts, they are encoded using 'utf-8'.
            if config.charset != 'utf-8':
                try:
                    page = unicode(page, 'utf-8', 'strict')
                    # Fit data into config.charset, replacing what won't
                    # fit. Better have few "?" in the name than crash.
                    page = page.encode(config.charset, 'replace')
                except UnicodeError:
                    pass

            # Decode from config.charset, replacing what can't be decoded.
            page = unicode(page, config.charset, 'replace')
            decoded.append(page)

        # Assemble decoded parts
        name = u'/'.join(decoded)
        return name

    def normalizePagename(self, name):
        """ Normalize page name

        Prevent creating page names with invisible characters or funny
        whitespace that might confuse the users or abuse the wiki, or
        just does not make sense.

        Restrict even more group pages, so they can be used inside acl lines.

        @param name: page name, unicode
        @rtype: unicode
        @return: decoded and sanitized page name
        """
        # Strip invalid characters
        name = config.page_invalid_chars_regex.sub(u'', name)

        # Split to pages and normalize each one
        pages = name.split(u'/')
        normalized = []
        for page in pages:
            # Ignore empty or whitespace only pages
            if not page or page.isspace():
                continue

            # Cleanup group pages.
            # Strip non alpha numeric characters, keep white space
            if wikiutil.isGroupPage(self, page):
                page = u''.join([c for c in page
                                 if c.isalnum() or c.isspace()])

            # Normalize white space. Each name can contain multiple
            # words separated with only one space. Split handle all
            # 30 unicode spaces (isspace() == True)
            page = u' '.join(page.split())

            normalized.append(page)

        # Assemble components into full pagename
        name = u'/'.join(normalized)
        return name

    def read(self, n):
        """ Read n bytes from input stream. """
        raise NotImplementedError

    def flush(self):
        """ Flush output stream. """
        pass

    def check_spider(self):
        """ check if the user agent for current request is a spider/bot """
        isSpider = False
        ua = self.getUserAgent()
        if ua and self.cfg.cache.ua_spiders:
            isSpider = self.cfg.cache.ua_spiders.search(ua) is not None
        return isSpider

    def isForbidden(self):
        """ check for web spiders and refuse anything except viewing """
        forbidden = 0
        # we do not have a parsed query string here, so we can just do simple matching
        qs = self.query_string
        action = self.action
        if ((qs != '' or self.request_method != 'GET') and
            action != 'rss_rc' and
            # allow spiders to get attachments and do 'show'
            not (action == 'AttachFile' and 'do=get' in qs) and
            action != 'show' and
            action != 'sitemap'
            ):
            forbidden = self.isSpiderAgent

        if not forbidden and self.cfg.hosts_deny:
            ip = self.remote_addr
            for host in self.cfg.hosts_deny:
                if host[-1] == '.' and ip.startswith(host):
                    forbidden = 1
                    logging.debug("hosts_deny (net): %s" % str(forbidden))
                    break
                if ip == host:
                    forbidden = 1
                    logging.debug("hosts_deny (ip): %s" % str(forbidden))
                    break
        return forbidden

    def setup_args(self):
        """ Return args dict
        First, we parse the query string (usually this is used in GET methods,
        but TwikiDraw uses ?action=AttachFile&do=savedrawing plus posted stuff).
        Second, we update what we got in first step by the stuff we get from
        the form (or by a POST). We invoke _setup_args_from_cgi_form to handle
        possible file uploads.
        """
        args = cgi.parse_qs(self.query_string, keep_blank_values=1)
        args = self.decodeArgs(args)
        # if we have form data (in a POST), those override the stuff we already have:
        if self.request_method == 'POST':
            postargs = self._setup_args_from_cgi_form()
            args.update(postargs)
        return args

    def _setup_args_from_cgi_form(self, form=None):
        """ Return args dict from a FieldStorage

        Create the args from a given form. Each key contain a list of values.
        This method usually gets overridden in classes derived from this - it
        is their task to call this method with an appropriate form parameter.

        @param form: a cgi.FieldStorage
        @rtype: dict
        @return: dict with form keys, each contains a list of values
        """
        args = {}
        for key in form:
            values = form[key]
            if not isinstance(values, list):
                values = [values]
            fixedResult = []
            for item in values:
                if isinstance(item, cgi.FieldStorage) and item.filename:
                    fixedResult.append(item.file) # open data tempfile
                    # Save upload file name in a separate key
                    args[key + '__filename__'] = item.filename
                else:
                    fixedResult.append(item.value)
            args[key] = fixedResult

        return self.decodeArgs(args)

    def decodeArgs(self, args):
        """ Decode args dict

        Decoding is done in a separate path because it is reused by
        other methods and sub classes.
        """
        decode = wikiutil.decodeUserInput
        result = {}
        for key in args:
            if key + '__filename__' in args:
                # Copy file data as is
                result[key] = args[key]
            elif key.endswith('__filename__'):
                result[key] = decode(args[key], self.decode_charsets)
            else:
                result[key] = [decode(value, self.decode_charsets) for value in args[key]]
        return result

    def getBaseURL(self):
        """ Return a fully qualified URL to this script. """
        return self.getQualifiedURL(self.getScriptname())

    def getQualifiedURL(self, uri=''):
        """ Return an absolute URL starting with schema and host.

        Already qualified urls are returned unchanged.

        @param uri: server rooted uri e.g /scriptname/pagename.
                    It must start with a slash. Must be ascii and url encoded.
        """
        import urlparse
        scheme = urlparse.urlparse(uri)[0]
        if scheme:
            return uri

        scheme = ('http', 'https')[self.is_ssl]
        result = "%s://%s%s" % (scheme, self.http_host, uri)

        # This might break qualified urls in redirects!
        # e.g. mapping 'http://netloc' -> '/'
        return wikiutil.mapURL(self, result)

    def getUserAgent(self):
        """ Get the user agent. """
        return self.http_user_agent

    def makeForbidden(self, resultcode, msg):
        statusmsg = {
            401: 'Authorization required',
            403: 'FORBIDDEN',
            404: 'Not found',
            503: 'Service unavailable',
        }
        headers = [
            'Status: %d %s' % (resultcode, statusmsg[resultcode]),
            'Content-Type: text/plain; charset=utf-8'
        ]
        # when surge protection triggered, tell bots to come back later...
        if resultcode == 503:
            headers.append('Retry-After: %d' % self.cfg.surge_lockout_time)
        self.emit_http_headers(headers)
        self.write(msg)
        self.forbidden = True

    def makeForbidden403(self):
        self.makeForbidden(403, 'You are not allowed to access this!\r\n')

    def makeUnavailable503(self):
        self.makeForbidden(503, "Warning:\r\n"
                   "You triggered the wiki's surge protection by doing too many requests in a short time.\r\n"
                   "Please make a short break reading the stuff you already got.\r\n"
                   "When you restart doing requests AFTER that, slow down or you might get locked out for a longer time!\r\n")

    def initTheme(self):
        """ Set theme - forced theme, user theme or wiki default """
        if self.cfg.theme_force:
            theme_name = self.cfg.theme_default
        else:
            theme_name = self.user.theme_name
        self.loadTheme(theme_name)

    def _try_redirect_spaces_page(self, pagename):
        if '_' in pagename and not self.page.exists():
            pname = pagename.replace('_', ' ')
            pg = Page(self, pname)
            if pg.exists():
                url = pg.url(self)
                self.http_redirect(url)
                return True
        return False

    def run(self):
        # Exit now if __init__ failed or request is forbidden
        if self.failed or self.forbidden or self._auth_redirected:
            # Don't sleep() here, it binds too much of our resources!
            return self.finish()

        _ = self.getText
        self.clock.start('run')

        self.initTheme()

        action_name = self.action
        if self.cfg.log_timing:
            self.timing_log(True, action_name)

        if action_name == 'xmlrpc':
            from MoinMoin import xmlrpc
            if self.query_string == 'action=xmlrpc':
                xmlrpc.xmlrpc(self)
            elif self.query_string == 'action=xmlrpc2':
                xmlrpc.xmlrpc2(self)
            if self.cfg.log_timing:
                self.timing_log(False, action_name)
            return self.finish()

        # parse request data
        try:
            # The last component in path_info is the page name, if any
            path = self.getPathinfo()

            # we can have all action URLs like this: /action/ActionName/PageName?action=ActionName&...
            # this is just for robots.txt being able to forbid them for crawlers
            prefix = self.cfg.url_prefix_action
            if prefix is not None:
                prefix = '/%s/' % prefix # e.g. '/action/'
                if path.startswith(prefix):
                    # remove prefix and action name
                    path = path[len(prefix):]
                    action, path = (path.split('/', 1) + ['', ''])[:2]
                    path = '/' + path

            if path.startswith('/'):
                pagename = self.normalizePagename(path)
            else:
                pagename = None

            # need to inform caches that content changes based on:
            # * cookie (even if we aren't sending one now)
            # * User-Agent (because a bot might be denied and get no content)
            # * Accept-Language (except if moin is told to ignore browser language)
            if self.cfg.language_ignore_browser:
                self.setHttpHeader("Vary: Cookie,User-Agent")
            else:
                self.setHttpHeader("Vary: Cookie,User-Agent,Accept-Language")

            # Handle request. We have these options:
            # 1. jump to page where user left off
            if not pagename and self.user.remember_last_visit and action_name == 'show':
                pagetrail = self.user.getTrail()
                if pagetrail:
                    # Redirect to last page visited
                    last_visited = pagetrail[-1]
                    wikiname, pagename = wikiutil.split_interwiki(last_visited)
                    if wikiname != 'Self':
                        wikitag, wikiurl, wikitail, error = wikiutil.resolve_interwiki(self, wikiname, pagename)
                        url = wikiurl + wikiutil.quoteWikinameURL(wikitail)
                    else:
                        url = Page(self, pagename).url(self)
                else:
                    # Or to localized FrontPage
                    url = wikiutil.getFrontPage(self).url(self)
                self.http_redirect(url)
                return self.finish()

            # 2. handle action
            else:
                # pagename could be empty after normalization e.g. '///' -> ''
                # Use localized FrontPage if pagename is empty
                if not pagename:
                    self.page = wikiutil.getFrontPage(self)
                else:
                    self.page = Page(self, pagename)
                    if self._try_redirect_spaces_page(pagename):
                        return self.finish()

                msg = None
                # Complain about unknown actions
                if not action_name in self.getKnownActions():
                    msg = _("Unknown action %(action_name)s.") % {
                            'action_name': wikiutil.escape(action_name), }

                # Disallow non available actions
                elif action_name[0].isupper() and not action_name in self.getAvailableActions(self.page):
                    msg = _("You are not allowed to do %(action_name)s on this page.") % {
                            'action_name': wikiutil.escape(action_name), }
                    if not self.user.valid:
                        # Suggest non valid user to login
                        msg += " " + _("Login and try again.")

                if msg:
                    self.theme.add_msg(msg, "error")
                    self.page.send_page()
                # Try action
                else:
                    from MoinMoin import action
                    handler = action.getHandler(self, action_name)
                    if handler is None:
                        msg = _("You are not allowed to do %(action_name)s on this page.") % {
                                'action_name': wikiutil.escape(action_name), }
                        if not self.user.valid:
                            # Suggest non valid user to login
                            msg += " " + _("Login and try again.")
                        self.theme.add_msg(msg, "error")
                        self.page.send_page()
                    else:
                        handler(self.page.page_name, self)

            # every action that didn't use to raise MoinMoinFinish must call this now:
            # self.theme.send_closing_html()

        except MoinMoinFinish:
            pass
        except RemoteClosedConnection:
            # at least clean up
            pass
        except SystemExit:
            raise # fcgi uses this to terminate a thread
        except Exception, err:
            try:
                # nothing we can do about further failures!
                self.fail(err)
            except:
                pass

        if self.cfg.log_timing:
            self.timing_log(False, action_name)

        return self.finish()

    def http_redirect(self, url):
        """ Redirect to a fully qualified, or server-rooted URL

        @param url: relative or absolute url, ascii using url encoding.
        """
        url = self.getQualifiedURL(url)
        self.emit_http_headers(["Status: 302 Found", "Location: %s" % url])

    def emit_http_headers(self, more_headers=[], testing=False):
        """ emit http headers after some preprocessing / checking

            Makes sure we only emit headers once.
            Encodes to ASCII if it gets unicode headers.
            Make sure we have exactly one Content-Type and one Status header.
            Make sure Status header string begins with a integer number.

            For emitting (testing == False), it calls the server specific
            _emit_http_headers method. For testing, it returns the result.

            @param more_headers: list of additional header strings
            @param testing: set to True by test code
        """
        user_headers = self.user_headers
        self.user_headers = []
        tracehere = ''.join(traceback.format_stack()[:-1])
        all_headers = [(hdr, tracehere) for hdr in more_headers] + user_headers

        if self.sent_headers:
            # Send headers only once
            logging.error("Attempt to send headers twice!")
            logging.error("First attempt:\n%s" % self.sent_headers)
            logging.error("Second attempt:\n%s" % tracehere)
            raise HeadersAlreadySentException("emit_http_headers has already been called before!")
        else:
            self.sent_headers = tracehere

        # assemble dict of http headers
        headers = {}
        traces = {}
        for header, trace in all_headers:
            if isinstance(header, unicode):
                header = header.encode('ascii')
            key, value = header.split(':', 1)
            lkey = key.lower()
            value = value.lstrip()
            if lkey in headers:
                if lkey in ['vary', 'cache-control', 'content-language', ]:
                    # these headers (list might be incomplete) allow multiple values
                    # that can be merged into a comma separated list
                    headers[lkey] = headers[lkey][0], '%s, %s' % (headers[lkey][1], value)
                    traces[lkey] = trace
                else:
                    logging.warning("Duplicate http header: %r (ignored)" % header)
                    logging.warning("Header added first at:\n%s" % traces[lkey])
                    logging.warning("Header added again at:\n%s" % trace)
            else:
                headers[lkey] = (key, value)
                traces[lkey] = trace

        if 'content-type' not in headers:
            headers['content-type'] = ('Content-type', 'text/html; charset=%s' % config.charset)

        if 'status' not in headers:
            headers['status'] = ('Status', '200 OK')
        else:
            # check if we got a valid status
            try:
                status = headers['status'][1]
                int(status.split(' ', 1)[0])
            except:
                logging.error("emit_http_headers called with invalid header Status: %r" % status)
                headers['status'] = ('Status', '500 Server Error - invalid status header')

        header_format = '%s: %s'
        st_header = header_format % headers['status']
        del headers['status']
        ct_header = header_format % headers['content-type']
        del headers['content-type']

        headers = [header_format % kv_tuple for kv_tuple in headers.values()] # make a list of strings
        headers = [st_header, ct_header] + headers # do NOT change order!
        if not testing:
            self._emit_http_headers(headers)
        else:
            return headers

    def _emit_http_headers(self, headers):
        """ server specific method to emit http headers.

            @param headers: a list of http header strings in this FIXED order:
                1. status header (always present and valid, e.g. "200 OK")
                2. content type header (always present)
                3. other headers (optional)
        """
        raise NotImplementedError

    def setHttpHeader(self, header):
        """ Save header for later send.

            Attention: although we use a list here, some implementations use a dict,
            thus multiple calls with the same header type do NOT work in the end!
        """
        # save a traceback with the header for duplicate bug reporting
        self.user_headers.append((header, ''.join(traceback.format_stack()[:-1])))

    def fail(self, err):
        """ Fail when we can't continue

        Send 500 status code with the error name. Reference:
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec6.html#sec6.1.1

        Log the error, then let failure module handle it.

        @param err: Exception instance or subclass.
        """
        self.failed = 1 # save state for self.run()
        # we should not generate the headers two times
        if not self.sent_headers:
            self.emit_http_headers(['Status: 500 MoinMoin Internal Error'])
        from MoinMoin import failure
        failure.handle(self, err)

    def make_unique_id(self, base, namespace=None):
        """
        Generates a unique ID using a given base name. Appends a running count to the base.

        Needs to stay deterministic!

        @param base: the base of the id
        @type base: unicode
        @param namespace: the namespace for the ID, used when including pages

        @returns: a unique (relatively to the namespace) ID
        @rtype: unicode
        """
        if not isinstance(base, unicode):
            base = unicode(str(base), 'ascii', 'ignore')
        if not namespace in self._page_ids:
            self._page_ids[namespace] = {}
        count = self._page_ids[namespace].get(base, -1) + 1
        self._page_ids[namespace][base] = count
        if not count:
            return base
        return u'%s-%d' % (base, count)

    def init_unique_ids(self):
        '''Initialise everything needed for unique IDs'''
        self._unique_id_stack = []
        self._page_ids = {None: {}}
        self.include_id = None
        self._include_stack = []

    def push_unique_ids(self):
        '''
        Used by the TOC macro, this ensures that the ID namespaces
        are reset to the status when the current include started.
        This guarantees that doing the ID enumeration twice results
        in the same results, on any level.
        '''
        self._unique_id_stack.append((self._page_ids, self.include_id))
        self.include_id, pids = self._include_stack[-1]
        # make a copy of the containing ID namespaces, that is to say
        # go back to the level we had at the previous include
        self._page_ids = {}
        for namespace in pids:
            self._page_ids[namespace] = pids[namespace].copy()

    def pop_unique_ids(self):
        '''
        Used by the TOC macro to reset the ID namespaces after
        having parsed the page for TOC generation and after
        printing the TOC.
        '''
        self._page_ids, self.include_id = self._unique_id_stack.pop()

    def begin_include(self, base):
        '''
        Called by the formatter when a document begins, which means
        that include causing nested documents gives us an include
        stack in self._include_id_stack.
        '''
        pids = {}
        for namespace in self._page_ids:
            pids[namespace] = self._page_ids[namespace].copy()
        self._include_stack.append((self.include_id, pids))
        self.include_id = self.make_unique_id(base)
        # if it's the page name then set it to None so we don't
        # prepend anything to IDs, but otherwise keep it.
        if self.page and self.page.page_name == self.include_id:
            self.include_id = None

    def end_include(self):
        '''
        Called by the formatter when a document ends, restores
        the current include ID to the previous one and discards
        the page IDs state we kept around for push_unique_ids().
        '''
        self.include_id, pids = self._include_stack.pop()

    def httpDate(self, when=None, rfc='1123'):
        """ Returns http date string, according to rfc2068

        See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-3.3

        A http 1.1 server should use only rfc1123 date, but cookie's
        "expires" field should use the older obsolete rfc850 date.

        Note: we can not use strftime() because that honors the locale
        and rfc2822 requires english day and month names.

        We can not use email.Utils.formatdate because it formats the
        zone as '-0000' instead of 'GMT', and creates only rfc1123
        dates. This is a modified version of email.Utils.formatdate
        from Python 2.4.

        @param when: seconds from epoch, as returned by time.time()
        @param rfc: conform to rfc ('1123' or '850')
        @rtype: string
        @return: http date conforming to rfc1123 or rfc850
        """
        if when is None:
            when = time.time()
        now = time.gmtime(when)
        month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
                 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][now.tm_mon - 1]
        if rfc == '1123':
            day = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now.tm_wday]
            date = '%02d %s %04d' % (now.tm_mday, month, now.tm_year)
        elif rfc == '850':
            day = ["Monday", "Tuesday", "Wednesday", "Thursday",
                    "Friday", "Saturday", "Sunday"][now.tm_wday]
            date = '%02d-%s-%s' % (now.tm_mday, month, str(now.tm_year)[-2:])
        else:
            raise ValueError("Invalid rfc value: %s" % rfc)

        return '%s, %s %02d:%02d:%02d GMT' % (day, date, now.tm_hour,
                                              now.tm_min, now.tm_sec)

    def disableHttpCaching(self, level=1):
        """ Prevent caching of pages that should not be cached.

        level == 1 means disabling caching when we have a cookie set
        level == 2 means completely disabling caching (used by Page*Editor)

        This is important to prevent caches break acl by providing one
        user pages meant to be seen only by another user, when both users
        share the same caching proxy.

        AVOID using no-cache and no-store for attachments as it is completely broken on IE!

        Details: http://support.microsoft.com/support/kb/articles/Q234/0/67.ASP
        """
        if level <= self.http_caching_disabled:
            return # only make caching stricter

        if level == 1:
            # Set Cache control header for http 1.1 caches
            # See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2109.html#sec-4.2.3
            # and http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-14.9
            #self.setHttpHeader('Cache-Control: no-cache="set-cookie", private, max-age=0')
            self.setHttpHeader('Cache-Control: private, must-revalidate, max-age=10')
        elif level == 2:
            self.setHttpHeader('Cache-Control: no-cache')

        # only do this once to avoid 'duplicate header' warnings
        # (in case the caching disabling is being made stricter)
        if not self.http_caching_disabled:
            # Set Expires for http 1.0 caches (does not support Cache-Control)
            when = time.time() - (3600 * 24 * 365)
            self.setHttpHeader('Expires: %s' % self.httpDate(when=when))

        # Set Pragma for http 1.0 caches
        # See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-14.32
        # DISABLED for level == 1 to fix IE https file attachment downloading trouble.
        if level == 2:
            self.setHttpHeader('Pragma: no-cache')

        self.http_caching_disabled = level

    def finish(self):
        """ General cleanup on end of request

        Delete circular references - all object that we create using self.name = class(self).
        This helps Python to collect these objects and keep our memory footprint lower.
        """
        for method in self._finishers:
            method(self)
        # only execute finishers once
        self._finishers = []

        for attr_name in [
            'editlog', # avoid leaking file handles for open edit-log
            'theme',
            'dicts',
            'user',
            'rootpage',
            'page',
            'html_formatter',
            'formatter',
            #'cfg', -- do NOT delattr cfg - it causes problems in the xapian indexing thread
            ]:
            try:
                delattr(self, attr_name)
            except:
                pass

    def add_finisher(self, method):
        self._finishers.append(method)

    # Debug ------------------------------------------------------------

    def debugEnvironment(self, env):
        """ Environment debugging aid """
        # Keep this one name per line so its easy to comment stuff
        names = [
#             'http_accept_language',
#             'http_host',
#             'http_referer',
#             'http_user_agent',
#             'is_ssl',
            'path_info',
            'query_string',
#             'remote_addr',
            'request_method',
#             'request_uri',
#             'saved_cookie',
            'script_name',
#             'server_name',
#             'server_port',
            ]
        names.sort()
        attributes = []
        for name in names:
            attributes.append('  %s = %r\n' % (name, getattr(self, name, None)))
        attributes = ''.join(attributes)

        environment = []
        names = env.keys()
        names.sort()
        for key in names:
            environment.append('  %s = %r\n' % (key, env[key]))
        environment = ''.join(environment)

        data = '\nRequest Attributes\n%s\nEnvironment\n%s' % (attributes, environment)
        f = open('/tmp/env.log', 'a')
        try:
            f.write(data)
        finally:
            f.close()

