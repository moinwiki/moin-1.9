# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Context objects which are passed thru instead of the classic
               request objects. Currently contains legacy wrapper code for
               a single request object.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import time, inspect

from werkzeug.utils import Headers, http_date, cached_property
from werkzeug.exceptions import Unauthorized, NotFound

from MoinMoin import i18n, error
from MoinMoin.config import multiconfig
from MoinMoin.formatter import text_html
from MoinMoin.request import RequestBase
from MoinMoin.web.request import Request, Response
from MoinMoin.web.utils import check_spider
from MoinMoin.web.exceptions import Forbidden, SurgeProtection

from MoinMoin import log
logging = log.getLogger(__name__)

class renamed_property(property):
    def __init__(self, name):
        property.__init__(self, lambda obj: getattr(obj, name))

class Context(object):
    def __init__(self, environ):
        self.environ = environ
        self.request = Request(environ)
        self.personalities = [self.__class__]
        self.initialize()

    def attr_getter(self, name):
        return super(Context, self).__getattr__(name)

    def attr_setter(self, name, value):
        return super(Context, self).__setattr__(name, value)        

    def __getattr__(self, name):
        logging.debug("GET: '%s' on '%r'", name, self)
        try:
            return self.attr_getter(name)
        except (AttributeError, KeyError):
            pass
        return super(Context, self).__getattribute__(name)

    def __setattr__(self, name, value):
        stack = inspect.stack()
        parent = stack[1]
        c, f, l = parent[3], parent[1], parent[0].f_lineno

        logging.debug("SET: '%s' on '%r' to '%r'", name, self, value)
        logging.debug("^^^: line %i, file '%s', caller '%s'", l, f, c)
        if name not in ('environ', 'request', 'personalities',
                        '__class__', '__dict__'):
            self.attr_setter(name, value)
        else:
            super(Context, self).__setattr__(name, value)

    def initialize(self):
        pass

    def become(self, cls):
        if self.__class__ is cls:
            return False
        elif cls in self.personalities:
            self.__class__ = cls
            return True
        else:
            self.personalities.append(cls)
            self.__class__ = cls
            self.initialize()
            return True

class XMLRPCContext(Context):
    pass

class HTTPContext(Context): #, RequestBase):
    """ Lowermost context for MoinMoin.

    Contains code related to manipulation of HTTP related data like:
    * Headers
    * Cookies
    * GET/POST/PUT/etc data
    """
    def initialize(self):
        self.response = Response()
        self._auth_redirected = False
        self.forbidden = 0
        self._cache_disabled = 0
        self.page = None
        self.user_headers = []
        self.sent_headers = None
        self.writestack = []

    def attr_getter(self, name):
        if hasattr(self.request, name):
            return getattr(self.request, name)
        else:
            return Context.attr_getter(self, name)
        
    def write(self, *data):
        if len(data) > 1:
            logging.warning("Some code still uses write with multiple arguments, "
                            "consider changing this soon")
        self.response.stream.writelines(data)
    
    # implementation of methods expected by RequestBase
    def send_file(self, fileobj, bufsize=8192, do_flush=None):
        self._sendfile = fileobj
        self._send_bufsize = bufsize



    def read(self, n=None):
        if n is None:
            return self.request.data
        else:
            return self.request.input_stream.read(n)

    def makeForbidden(self, resultcode, msg):
        status = { 401: Unauthorized,
                   403: Forbidden,
                   404: NotFound,
                   503: SurgeProtection }
        raise status[resultcode](msg)

    def setHttpHeader(self, header):
        header, value = header.split(':', 1)
        self.response.headers.add(header, value)

    def disableHttpCaching(self, level=1):
        if level <= self._cache_disabled:
            return
        
        if level == 1:
            self.response.headers.add('Cache-Control', 'private, must-revalidate, mag-age=10')
        elif level == 2:
            self.response.headers.add('Cache-Control', 'no-cache')
            self.response.headers.set('Pragma', 'no-cache')

        if not self._cache_disabled:
            when = time.time() - (3600 * 24 * 365)
            self.response.headers.set('Expires', http_date(when))

        self._cache_disabled = level

    def _emit_http_headers(self, headers):
        st_header, other_headers = headers[0], headers[1:]
        self.response.status = st_header[8:] # strip 'Status: '
        for header in other_headers:
            key, value = header.split(':', 1)
            self.response.headers.add(key, value)

    # legacy compatibility & properties
    # e.g. different names in werkzeug
    def lang(self):
        if i18n.languages is None:
            i18n.i18n_init(self)

        lang = None
        
        if i18n.languages and not self.cfg.language_ignore_browser:
            for l in self.accept_languages:
                if l in i18n.languages:
                    lang = l
                    break

        if lang is None and self.cfg.language_default in i18n.languages:
            lang = self.cfg.language_default
        else:
            lang = 'en'
        return lang
    lang = cached_property(lang)

    def getText(self):
        lang = self.lang
            
        def _(text, i18n=i18n, request=self, lang=lang, **kw):
            return i18n.getText(text, request, lang, **kw)
        return _
    getText = cached_property(getText)

    def action(self):
        return self.values.get('action','show')
    action = cached_property(action)

    def rev(self):
        try:
            return int(self.values['rev'])
        except:
            return None
    rev = cached_property(rev)

    def cfg(self):
        try:
            self.clock.start('load_multi_cfg')
            cfg = multiconfig.getConfig(self.url)
            self.clock.stop('load_multi_cfg')
            return cfg
        except error.NoConfigMatchedError:
            raise NotFound('<p>No wiki configuration matching the URL found!</p>')
    cfg = cached_property(cfg)

    def isSpiderAgent(self):
        return check_spider(self.user_agent, self.cfg)
    isSpiderAgent = cached_property(isSpiderAgent)


    cookie = renamed_property('cookies')
    script_name = renamed_property('script_root')
    path_info = renamed_property('path')
    is_ssl = renamed_property('is_secure')
    request_method = renamed_property('method')

class RenderContext(HTTPContext):
    """ Context for rendering content
    
    Contains code related to the representation of pages:
    * formatters
    * theme
    * page
    * output redirection
    """
    def initialize(self):
        self.pragma = {}
        self.mode_getpagelinks = 0
        self.parsePageLinks_running = {}

        if i18n.languages is None:
            i18n.i18n_init(self)

    def html_formatter(self):
        return text_html.Formatter(self)
    html_formatter = cached_property(html_formatter)

    def formatter(self):
        return self.html_formatter
    formatter = cached_property(formatter)

    def content_lang(self):
        return self.cfg.language_default
    content_lang = cached_property(content_lang)
    
    def lang(self):
        if self.user.valid and self.user.language:
            return self.user.language
        else:
            return super(RenderContext, self).lang
    lang = cached_property(lang)

    def rootpage(self):
        from MoinMoin.Page import RootPage
        return RootPage(self)
    rootpage = cached_property(rootpage)

    def dicts(self):
        """ Lazy initialize the dicts on the first access """
        from MoinMoin import wikidicts
        dicts = wikidicts.GroupDict(self)
        dicts.load_dicts()
        return dicts
    dicts = cached_property(dicts)

