# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RequestBase Implementation

    @copyright: 2001-2003 by Jürgen Hermann <jh@web.de>,
                2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, re, time, sys, cgi, StringIO
import copy
from MoinMoin import config, wikiutil, user, caching
from MoinMoin.util import IsWin9x


# Exceptions -----------------------------------------------------------

class MoinMoinFinish(Exception):
    """ Raised to jump directly to end of run() function, where finish is called """
    pass

# Timing ---------------------------------------------------------------

class Clock:
    """ Helper class for code profiling
        we do not use time.clock() as this does not work across threads
    """

    def __init__(self):
        self.timings = {'total': time.time()}

    def start(self, timer):
        self.timings[timer] = time.time() - self.timings.get(timer, 0)

    def stop(self, timer):
        self.timings[timer] = time.time() - self.timings[timer]

    def value(self, timer):
        return "%.3f" % (self.timings[timer], )

    def dump(self):
        outlist = []
        for timing in self.timings.items():
            outlist.append("%s = %.3fs" % timing)
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

    # Header set to force misbehaved proxies and browsers to keep their
    # hands off a page
    # Details: http://support.microsoft.com/support/kb/articles/Q234/0/67.ASP
    nocache = [
        "Pragma: no-cache",
        "Cache-Control: no-cache",
        "Expires: -1",
    ]

    # Defaults (used by sub classes)
    http_accept_language = 'en'
    server_name = 'localhost'
    server_port = '80'

    # Extra headers we support. Both standalone and twisted store
    # headers as lowercase.
    moin_location = 'x-moin-location'
    proxy_host = 'x-forwarded-host'

    def __init__(self, properties={}):
        # Decode values collected by sub classes
        self.path_info = self.decodePagename(self.path_info)

        self.failed = 0
        self._available_actions = None
        self._known_actions = None

        # Pages meta data that we collect in one request
        self.pages = {}

        self.sent_headers = 0
        self.user_headers = []
        self.cacheable = 0 # may this output get cached by http proxies/caches?
        self.page = None
        self._dicts = None

        # Fix dircaching problems on Windows 9x
        if IsWin9x():
            import dircache
            dircache.reset()

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
            # order is important here!
            self.__dict__.update(properties)
            self._load_multi_cfg()

            self.isSpiderAgent = self.check_spider()

            # Set decode charsets.  Input from the user is always in
            # config.charset, which is the page charsets. Except
            # path_info, which may use utf-8, and handled by decodePagename.
            self.decode_charsets = [config.charset]

            # hierarchical wiki - set rootpage
            from MoinMoin.Page import Page
            #path = self.getPathinfo()
            #if path.startswith('/'):
            #    pages = path[1:].split('/')
            #    if 0: # len(path) > 1:
            #        ## breaks MainPage/SubPage on flat storage
            #        rootname = u'/'.join(pages[:-1])
            #    else:
            #        # this is the usual case, as it ever was...
            #        rootname = u""
            #else:
            #    # no extra path after script name
            #    rootname = u""

            if self.query_string.startswith('action=xmlrpc'):
                self.args = {}
                self.form = {}
                self.action = 'xmlrpc'
            else:
                self.args = self.form = self.setup_args()
                self.action = self.form.get('action', ['show'])[0]

            rootname = u''
            self.rootpage = Page(self, rootname, is_rootpage=1)

            from MoinMoin import i18n
            self.i18n = i18n
            i18n.i18n_init(self)

            self.user = self.get_user_from_form()

            if self.action != 'xmlrpc':
                if not self.forbidden and self.isForbidden():
                    self.makeForbidden403()
                if not self.forbidden and self.surge_protect():
                    self.makeUnavailable503()

            self.logger = None
            self.pragma = {}
            self.mode_getpagelinks = 0

            self.lang = i18n.requestLanguage(self)
            # Language for content. Page content should use the wiki default lang,
            # but generated content like search results should use the user language.
            self.content_lang = self.cfg.language_default
            self.getText = lambda text, i18n=self.i18n, request=self, lang=self.lang, **kv: i18n.getText(text, request, lang, kv.get('formatted', True))

            self.opened_logs = 0
            self.reset()

    def surge_protect(self):
        """ check if someone requesting too much from us """
        validuser = self.user.valid
        current_id = validuser and self.user.name or self.remote_addr
        if not validuser and current_id.startswith('127.'): # localnet
            return False
        current_action = self.action

        limits = self.cfg.surge_action_limits
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
                    except StandardError, err:
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
        except StandardError, err:
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
            from MoinMoin import multiconfig
            self.cfg = multiconfig.getConfig(self.url)

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
                accept_charset.find('iso-8859-1') < 0):
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
        self.http_accept_language = env.get('HTTP_ACCEPT_LANGUAGE',
                                            self.http_accept_language)
        self.server_name = env.get('SERVER_NAME', self.server_name)
        self.server_port = env.get('SERVER_PORT', self.server_port)
        self.saved_cookie = env.get('HTTP_COOKIE', '')
        self.script_name = env.get('SCRIPT_NAME', '')
        self.path_info = env.get('PATH_INFO', '')
        self.query_string = env.get('QUERY_STRING', '')
        self.request_method = env.get('REQUEST_METHOD', None)
        self.remote_addr = env.get('REMOTE_ADDR', '')
        self.http_user_agent = env.get('HTTP_USER_AGENT', '')

        # REQUEST_URI is not part of CGI spec, but an addition of Apache.
        self.request_uri = env.get('REQUEST_URI', '')

        # Values that need more work
        self.setHttpReferer(env.get('HTTP_REFERER'))
        self.setIsSSL(env)
        self.setHost(env.get('HTTP_HOST'))
        self.fixURI(env)
        self.setURL(env)

        ##self.debugEnvironment(env)

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
        if os.name == 'nt' and server_software.find('Apache/') != -1:
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
        login = self.form.has_key('login')
        logout = self.form.has_key('logout')
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

        self._all_pages = None
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

    def getPageNameFromQueryString(self):
        """ Try to get pagename from the query string
        
        Support urls like http://netloc/script/?page_name. Allow
        solving path_info encoding problems by calling with the page
        name as a query.
        """
        pagename = wikiutil.url_unquote(self.query_string, want_unicode=False)
        pagename = self.decodePagename(pagename)
        pagename = self.normalizePagename(pagename)
        return pagename

    def getKnownActions(self):
        """ Create a dict of avaiable actions

        Return cached version if avaiable.
       
        @rtype: dict
        @return: dict of all known actions
        """
        try:
            self.cfg._known_actions # check
        except AttributeError:
            from MoinMoin import action
            # Add built in actions
            actions = [name[3:] for name in action.__dict__ if name.startswith('do_')]

            # Add plugins           
            dummy, plugins = action.getPlugins(self)
            actions.extend(plugins)

            # Add extensions
            actions.extend(action.extension_actions)

            # TODO: Use set when we require Python 2.3
            actions = dict(zip(actions, [''] * len(actions)))
            self.cfg._known_actions = actions

        # Return a copy, so clients will not change the dict.
        return self.cfg._known_actions.copy()

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
            for key in actions.keys():
                if key[0].islower():
                    del actions[key]

            # Filter wiki excluded actions
            for key in self.cfg.actions_excluded:
                if key in actions:
                    del actions[key]

            # Filter actions by page type, acl and user state
            excluded = []
            if ((page.isUnderlayPage() and not page.isStandardPage()) or
                not self.user.may.write(page.page_name) or
                not self.user.may.delete(page.page_name)):
                # Prevent modification of underlay only pages, or pages
                # the user can't write and can't delete
                excluded = [u'RenamePage', u'DeletePage', ] # AttachFile must NOT be here!
            for key in excluded:
                if key in actions:
                    del actions[key]

            self._available_actions = actions

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
        """ Log to stderr, which may be error.log """
        msg = msg.strip()
        # Encode unicode msg
        if isinstance(msg, unicode):
            msg = msg.encode(config.charset)
        # Add time stamp
        msg = '[%s] %s\n' % (time.asctime(), msg)
        sys.stderr.write(msg)

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
        spiders = self.cfg.ua_spiders
        if spiders:
            ua = self.getUserAgent()
            if ua:
                isSpider = re.search(spiders, ua, re.I) is not None
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
            action != 'show'
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

    def setup_args(self, form=None):
        """ Return args dict 
        First, we parse the query string (usually this is used in GET methods,
        but TwikiDraw uses ?action=AttachFile&do=savedrawing plus posted stuff).
        Second, we update what we got in first step by the stuff we get from
        the form (or by a POST). We invoke _setup_args_from_cgi_form to handle
        possible file uploads.
        
        Warning: calling with a form might fail, depending on the type of the
        request! Only the request knows which kind of form it can handle.
        
        TODO: The form argument should be removed in 1.5.
        """
        args = cgi.parse_qs(self.query_string, keep_blank_values=1)
        args = self.decodeArgs(args)
        # if we have form data (e.g. in a POST), those override the stuff we already have:
        if form is not None or self.request_method == 'POST':
            postargs = self._setup_args_from_cgi_form(form)
            args.update(postargs)
        return args

    def _setup_args_from_cgi_form(self, form=None):
        """ Return args dict from a FieldStorage
        
        Create the args from a standard cgi.FieldStorage or from given form.
        Each key contain a list of values.

        @param form: a cgi.FieldStorage
        @rtype: dict
        @return: dict with form keys, each contains a list of values
        """
        if form is None:
            form = cgi.FieldStorage()

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
            503: 'Service unavailable',
        }
        headers = [
            'Status: %d %s' % (resultcode, statusmsg[resultcode]),
            'Content-Type: text/plain'
        ]
        # when surge protection triggered, tell bots to come back later...
        if resultcode == 503:
            headers.append('Retry-After: %d' % self.cfg.surge_lockout_time)
        self.http_headers(headers)
        self.setResponseCode(resultcode)
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

        self.open_logs()
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
                page = wikiutil.getSysPage(self, 'UserPreferences')
                page.send_page(self, msg=msg)

            # 2. Or jump to page where user left off
            elif not pagename and self.user.remember_last_visit:
                pagetrail = self.user.getTrail()
                if pagetrail:
                    # Redirect to last page visited
                    if ":" in pagetrail[-1]:
                        wikitag, wikiurl, wikitail, error = wikiutil.resolve_wiki(self, pagetrail[-1])
                        url = wikiurl + wikiutil.quoteWikinameURL(wikitail)
                    else:
                        url = Page(self, pagetrail[-1]).url(self)
                else:
                    # Or to localized FrontPage
                    url = wikiutil.getFrontPage(self).url(self)
                self.http_redirect(url)
                return self.finish()

            # 3. Or handle action
            else:
                if not pagename and self.query_string:
                    pagename = self.getPageNameFromQueryString()
                # pagename could be empty after normalization e.g. '///' -> ''
                # Use localized FrontPage if pagename is empty
                if not pagename:
                    self.page = wikiutil.getFrontPage(self)
                else:
                    self.page = Page(self, pagename)

                # Complain about unknown actions
                if not action_name in self.getKnownActions():
                    self.http_headers()
                    self.write(u'<html><body><h1>Unknown action %s</h1></body>' % wikiutil.escape(action_name))

                # Disallow non available actions
                elif action_name[0].isupper() and not action_name in self.getAvailableActions(self.page):
                    # Send page with error
                    msg = _("You are not allowed to do %s on this page.") % wikiutil.escape(action_name)
                    if not self.user.valid:
                        # Suggest non valid user to login
                        msg += " " + _("Login and try again.", formatted=0)
                    self.page.send_page(self, msg=msg)

                # Try action
                else:
                    from MoinMoin import action
                    handler = action.getHandler(self, action_name)
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
        self.http_headers(["Status: 302 Found", "Location: %s" % url])

    def setHttpHeader(self, header):
        """ Save header for later send.
        
            Attention: although we use a list here, some implementations use a dict,
            thus multiple calls with the same header type do NOT work in the end!
        """
        self.user_headers.append(header)

    def setResponseCode(self, code, message=None):
        pass

    def fail(self, err):
        """ Fail when we can't continue

        Send 500 status code with the error name. Reference: 
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec6.html#sec6.1.1

        Log the error, then let failure module handle it. 

        @param err: Exception instance or subclass.
        """
        self.failed = 1 # save state for self.run()            
        self.http_headers(['Status: 500 MoinMoin Internal Error'])
        self.setResponseCode(500)
        self.log('%s: %s' % (err.__class__.__name__, str(err)))
        from MoinMoin import failure
        failure.handle(self)

    def open_logs(self):
        pass

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

    def disableHttpCaching(self):
        """ Prevent caching of pages that should not be cached

        This is important to prevent caches break acl by providing one
        user pages meant to be seen only by another user, when both users
        share the same caching proxy.
        """
        # Run only once
        if hasattr(self, 'http_caching_disabled'):
            return
        self.http_caching_disabled = 1

        # Set Cache control header for http 1.1 caches
        # See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2109.html#sec-4.2.3
        # and http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-14.9
        self.setHttpHeader('Cache-Control: no-cache="set-cookie", private, max-age=0')

        # Set Expires for http 1.0 caches (does not support Cache-Control)
        yearago = time.time() - (3600 * 24 * 365)
        self.setHttpHeader('Expires: %s' % self.httpDate(when=yearago))

        # Set Pragma for http 1.0 caches
        # See http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2068.html#sec-14.32
        self.setHttpHeader('Pragma: no-cache')

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

        data = '\nRequest Attributes\n%s\nEnviroment\n%s' % (attributes, environment)
        f = open('/tmp/env.log', 'a')
        try:
            f.write(data)
        finally:
            f.close()

