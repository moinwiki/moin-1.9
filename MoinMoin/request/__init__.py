# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RequestBase Implementation

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, re, time, sys, cgi, StringIO
import logging
import copy

try:
    set
except:
    from sets import Set as set

from MoinMoin import config, wikiutil, user, caching, error
from MoinMoin.config import multiconfig
from MoinMoin.util import IsWin9x

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


# Timing ---------------------------------------------------------------

class Clock:
    """ Helper class for code profiling
        we do not use time.clock() as this does not work across threads
        This is not thread-safe when it comes to multiple starts for one timer.
        It is possible to recursively call the start and stop methods, you
        should just ensure that you call them often enough :)
    """

    def __init__(self):
        self.timings = {}
        self.states = {}

    def _get_name(timer, generation):
        if generation == 0:
            return timer
        else:
            return "%s|%i" % (timer, generation)
    _get_name = staticmethod(_get_name)

    def start(self, timer):
        state = self.states.setdefault(timer, -1)
        new_level = state + 1
        name = Clock._get_name(timer, new_level)
        self.timings[name] = time.time() - self.timings.get(name, 0)
        self.states[timer] = new_level

    def stop(self, timer):
        state = self.states.setdefault(timer, -1)
        if state >= 0: # timer is active
            name = Clock._get_name(timer, state)
            self.timings[name] = time.time() - self.timings[name]
            self.states[timer] = state - 1

    def value(self, timer):
        base_timer = timer.split("|")[0]
        state = self.states.get(base_timer, None)
        if state == -1:
            result = "%.3fs" % self.timings[timer]
        elif state is None:
            result = "- (%s)" % state
        else:
            #print "Got state %r" % state
            result = "%.3fs (still running)" % (time.time() - self.timings[timer])
        return result

    def dump(self):
        outlist = []
        for timer in self.timings:
            value = self.value(timer)
            outlist.append("%s = %s" % (timer, value))
        outlist.sort()
        return outlist


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
    proxy_host = 'x-forwarded-host'

    def __init__(self, properties={}):

        # twistd's daemonize() overrides our umask, so we reset it here every
        # request. we do it for all request types to avoid similar problems.
        set_umask()

        # Decode values collected by sub classes
        self.path_info = self.decodePagename(self.path_info)

        self.failed = 0
        self._available_actions = None
        self._known_actions = None

        # Pages meta data that we collect in one request
        self.pages = {}

        self.user_headers = []
        self.cacheable = 0 # may this output get cached by http proxies/caches?
        self.http_caching_disabled = 0 # see disableHttpCaching()
        self.page = None
        self._dicts = None

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
                self._load_multi_cfg()
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
                self.args = self.form = self.setup_args()
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

            self.user = self.get_user_from_form()

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
            self.getText = lambda text, i18n=self.i18n, request=self, lang=self.lang, **kv: i18n.getText(text, request, lang, kv.get('formatted', True))

            self.reset()
            self.clock.stop('base__init__')

    def surge_protect(self, kick_him=False):
        """ check if someone requesting too much from us,
            if kick_him is True, we unconditionally blacklist the current user/ip
        """
        limits = self.cfg.surge_action_limits
        if not limits:
            return False
                                    
        validuser = self.user.valid
        current_id = validuser and self.user.name or self.remote_addr
        if not validuser and current_id.startswith('127.'): # localnet
            return False
        current_action = self.action

        default_limit = self.cfg.surge_action_limits.get('default', (30, 60))

        now = int(time.time())
        surgedict = {}
        surge_detected = False

        try:
            # if we have common farm users, we could also use scope='farm':
            cache = caching.CacheEntry(self, 'surgeprotect', 'surge-log', scope='wiki')
            if cache.exists():
                data = cache.content()
                data = data.split("\n")
                for line in data:
                    try:
                        id, t, action, surge_indicator = line.split("\t")
                        t = int(t)
                        maxnum, dt = limits.get(action, default_limit)
                        if t >= now - dt:
                            events = surgedict.setdefault(id, copy.copy({}))
                            timestamps = events.setdefault(action, copy.copy([]))
                            timestamps.append((t, surge_indicator))
                    except StandardError:
                        pass

            maxnum, dt = limits.get(current_action, default_limit)
            events = surgedict.setdefault(current_id, copy.copy({}))
            timestamps = events.setdefault(current_action, copy.copy([]))
            surge_detected = len(timestamps) > maxnum

            surge_indicator = surge_detected and "!" or ""
            timestamps.append((now, surge_indicator))
            if surge_detected:
                if len(timestamps) < maxnum * 2:
                    timestamps.append((now + self.cfg.surge_lockout_time, surge_indicator)) # continue like that and get locked out

            if current_action != 'AttachFile': # don't add AttachFile accesses to all or picture galleries will trigger SP
                current_action = 'all' # put a total limit on user's requests
                maxnum, dt = limits.get(current_action, default_limit)
                events = surgedict.setdefault(current_id, copy.copy({}))
                timestamps = events.setdefault(current_action, copy.copy([]))

                if kick_him: # ban this guy, NOW
                    timestamps.extend([(now + self.cfg.surge_lockout_time, "!")] * (2*maxnum))

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

        return surge_detected

    def getDicts(self):
        """ Lazy initialize the dicts on the first access """
        if self._dicts is None:
            from MoinMoin import wikidicts
            dicts = wikidicts.GroupDict(self)
            dicts.scandicts()
            self._dicts = dicts
        return self._dicts

    def delDicts(self):
        """ Delete the dicts, used by some tests """
        del self._dicts
        self._dicts = None

    dicts = property(getDicts, None, delDicts)

    def _load_multi_cfg(self):
        # protect against calling multiple times
        if not hasattr(self, 'cfg'):
            self.clock.start('load_multi_cfg')
            self.cfg = multiconfig.getConfig(self.url)
            self.clock.stop('load_multi_cfg')

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
                           env.get('HTTPS') == 'on')

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
        # If we serve on localhost:8000 and use a proxy on
        # example.com/wiki, our urls will be example.com/wiki/pagename
        # Same for the wiki config - they must use the proxy url.
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

    def get_user_from_form(self):
        """ read the maybe present UserPreferences form and call get_user with the values """
        name = self.form.get('name', [None])[0]
        password = self.form.get('password', [None])[0]
        login = 'login' in self.form
        logout = 'logout' in self.form
        u = self.get_user_default_unknown(name=name, password=password,
                                          login=login, logout=logout,
                                          user_obj=None)
        return u

    def get_user_default_unknown(self, **kw):
        """ call do_auth and if it doesnt return a user object, make some "Unknown User" """
        user_obj = self.get_user_default_None(**kw)
        if user_obj is None:
            user_obj = user.User(self, auth_method="request:427")
        return user_obj

    def get_user_default_None(self, **kw):
        """ loop over auth handlers, return a user obj or None """
        name = kw.get('name')
        password = kw.get('password')
        login = kw.get('login')
        logout = kw.get('logout')
        user_obj = kw.get('user_obj')
        for auth in self.cfg.auth:
            user_obj, continue_flag = auth(self, name=name, password=password,
                                           login=login, logout=logout, user_obj=user_obj)
            if not continue_flag:
                break
        return user_obj

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
        self._page_ids = {}
        # keeps track of pagename/heading combinations
        # parsers should use this dict and not a local one, so that
        # macros like TableOfContents in combination with Include can work
        self._page_headings = {}

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
            # Add actions for existing pages only, including deleted pages.
            # Fix *OnNonExistingPage bugs.
            if not (page.exists(includeDeleted=1) and self.user.may.read(page.page_name)):
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
        buffer = StringIO.StringIO()
        self.redirect(buffer)
        try:
            function(*args, **kw)
        finally:
            self.redirect()
        text = buffer.getvalue()
        buffer.close()
        return text

    def redirect(self, file=None):
        """ Redirect output to file, or restore saved output """
        if file:
            self.writestack.append(self.write)
            self.write = file.write
        else:
            self.write = self.writestack.pop()

    def reset_output(self):
        """ restore default output method
            destroy output stack
            (useful for error messages)
        """
        if self.writestack:
            self.write = self.writestack[0]
            self.writestack = []

    def log(self, msg):
        """ Log msg to logging framework """
        msg = msg.strip()
        # Encode unicode msg
        if isinstance(msg, unicode):
            msg = msg.encode(config.charset)
        logging.info(msg)

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
                self.log("Unicode error on: %s" % repr(d))
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
        raise NotImplementedError

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
                    #self.log("hosts_deny (net): %s" % str(forbidden))
                    break
                if ip == host:
                    forbidden = 1
                    #self.log("hosts_deny (ip): %s" % str(forbidden))
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
                fixedResult.append(item.value)
                if isinstance(item, cgi.FieldStorage) and item.filename:
                    # Save upload file name in a separate key
                    args[key + '__filename__'] = item.filename
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

    def run(self):
        # Exit now if __init__ failed or request is forbidden
        if self.failed or self.forbidden:
            # Don't sleep() here, it binds too much of our resources!
            return self.finish()

        _ = self.getText
        self.clock.start('run')

        from MoinMoin.Page import Page
        from MoinMoin.formatter.text_html import Formatter
        self.html_formatter = Formatter(self)
        self.formatter = self.html_formatter

        action_name = self.action
        if action_name == 'xmlrpc':
            from MoinMoin import xmlrpc
            if self.query_string == 'action=xmlrpc':
                xmlrpc.xmlrpc(self)
            elif self.query_string == 'action=xmlrpc2':
                xmlrpc.xmlrpc2(self)
            return self.finish()

        # parse request data
        try:
            self.initTheme()

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
                    action, path = path.split('/', 1)
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
            # 1. If user has a bad user name, delete its bad cookie and
            # send him to UserPreferences to make a new account.
            if not user.isValidName(self, self.user.name):
                msg = _("""Invalid user name {{{'%s'}}}.
Name may contain any Unicode alpha numeric character, with optional one
space between words. Group page name is not allowed.""") % self.user.name
                self.user = self.get_user_default_unknown(name=self.user.name, logout=True)
                page = wikiutil.getLocalizedPage(self, 'UserPreferences')
                page.send_page(msg=msg)

            # 2. Or jump to page where user left off
            elif not pagename and self.user.remember_last_visit:
                pagetrail = self.user.getTrail()
                if pagetrail:
                    # Redirect to last page visited
                    if ":" in pagetrail[-1]:
                        wikitag, wikiurl, wikitail, error = wikiutil.resolve_wiki(self, pagetrail[-1])
                        url = wikiurl + wikiutil.quoteWikinameURL(wikitail)
                    else:
                        url = Page(self, pagetrail[-1]).url(self, relative=False)
                else:
                    # Or to localized FrontPage
                    url = wikiutil.getFrontPage(self).url(self, relative=False)
                self.http_redirect(url)
                return self.finish()

            # 3. Or handle action
            else:
                # pagename could be empty after normalization e.g. '///' -> ''
                # Use localized FrontPage if pagename is empty
                if not pagename:
                    self.page = wikiutil.getFrontPage(self)
                else:
                    self.page = Page(self, pagename)

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
                        msg += " " + _("Login and try again.", formatted=0)

                if msg:
                    self.page.send_page(msg=msg)

                # Try action
                else:
                    from MoinMoin import action
                    handler = action.getHandler(self, action_name)
                    if handler is None:
                        msg = _("You are not allowed to do %(action_name)s on this page.") % {
                                'action_name': wikiutil.escape(action_name), }
                        if not self.user.valid:
                            # Suggest non valid user to login
                            msg += " " + _("Login and try again.", formatted=0)
                        self.page.send_page(msg=msg)
                    else:
                        handler(self.page.page_name, self)

            # every action that didn't use to raise MoinMoinNoFooter must call this now:
            # self.theme.send_closing_html()

        except MoinMoinFinish:
            pass
        except Exception, err:
            self.fail(err)

        return self.finish()

    def http_redirect(self, url):
        """ Redirect to a fully qualified, or server-rooted URL
        
        @param url: relative or absolute url, ascii using url encoding.
        """
        url = self.getQualifiedURL(url)
        self.emit_http_headers(["Status: 302 Found", "Location: %s" % url])

    def http_headers(self, more_headers=[]):
        """ wrapper for old, deprecated http_headers call,
            new code only calls emit_http_headers.
            Remove in moin 1.7.
        """
        self.emit_http_headers(more_headers)

    def emit_http_headers(self, more_headers=[]):
        """ emit http headers after some preprocessing / checking

            Makes sure we only emit headers once.
            Encodes to ASCII if it gets unicode headers.
            Make sure we have exactly one Content-Type and one Status header.
            Make sure Status header string begins with a integer number.
        
            For emitting, it calls the server specific _emit_http_headers
            method.

            @param more_headers: list of additional header strings
        """
        user_headers = getattr(self, 'user_headers', [])
        self.user_headers = []
        all_headers = more_headers + user_headers

        # Send headers only once
        sent_headers = getattr(self, 'sent_headers', 0)
        sent_headers += 1
        self.sent_headers = sent_headers
        if sent_headers > 1:
            raise HeadersAlreadySentException("emit_http_headers called multiple (%d) times! Headers: %r" % (sent_headers, all_headers))
        #else:
        #    self.log("Notice: emit_http_headers called first time. Headers: %r" % all_headers)

        content_type = None
        status = None
        headers = []
        # assemble complete list of http headers
        for header in all_headers:
            if isinstance(header, unicode):
                header = header.encode('ascii')
            key, value = header.split(':', 1)
            lkey = key.lower()
            value = value.lstrip()
            if content_type is None and lkey == "content-type":
                content_type = value
            elif status is None and lkey == "status":
                status = value
            else:
                headers.append(header)

        if content_type is None:
            content_type = "text/html; charset=%s" % config.charset
        ct_header = "Content-type: %s" % content_type

        if status is None:
            status = "200 OK"
        try:
            int(status.split(" ", 1)[0])
        except:
            self.log("emit_http_headers called with invalid header Status: %s" % status)
            status = "500 Server Error - invalid status header"
        st_header = "Status: %s" % status

        headers = [st_header, ct_header] + headers # do NOT change order!
        self._emit_http_headers(headers)

        #from pprint import pformat
        #sys.stderr.write(pformat(headers))

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
        self.user_headers.append(header)

    def setResponseCode(self, code, message=None):
        """ DEPRECATED, will vanish in moin 1.7,
            just use a Status: <code> <message> header and emit_http_headers.
        """
        pass

    def fail(self, err):
        """ Fail when we can't continue

        Send 500 status code with the error name. Reference: 
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec6.html#sec6.1.1

        Log the error, then let failure module handle it. 

        @param err: Exception instance or subclass.
        """
        self.failed = 1 # save state for self.run()            
        # we should not generate the headers two times
        if not getattr(self, 'sent_headers', 0):
            self.emit_http_headers(['Status: 500 MoinMoin Internal Error'])
        from MoinMoin import failure
        failure.handle(self, err)

    def makeUniqueID(self, base):
        """
        Generates a unique ID using a given base name. Appends a running count to the base.

        @param base: the base of the id
        @type base: unicode

        @returns: an unique id
        @rtype: unicode
        """
        if not isinstance(base, unicode):
            base = unicode(str(base), 'ascii', 'ignore')
        count = self._page_ids.get(base, -1) + 1
        self._page_ids[base] = count
        if count == 0:
            return base
        return u'%s_%04d' % (base, count)

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
        try:
            del self.user
            del self.theme
            del self.dicts
        except:
            pass

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

