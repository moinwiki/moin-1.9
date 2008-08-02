# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Context objects which are passed thru instead of the classic
               request objects. Currently contains legacy wrapper code for
               a single request object.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import time, inspect, StringIO, sys

from werkzeug.utils import Headers, http_date, create_environ, redirect 
from werkzeug.exceptions import Unauthorized, NotFound, abort

from MoinMoin import i18n, error, user, config
from MoinMoin.config import multiconfig
from MoinMoin.formatter import text_html
from MoinMoin.theme import load_theme_fallback
from MoinMoin.util.clock import Clock
from MoinMoin.web.request import Request, MoinMoinFinish
from MoinMoin.web.utils import check_spider, UniqueIDGenerator
from MoinMoin.web.exceptions import Forbidden, SurgeProtection

from MoinMoin import log
logging = log.getLogger(__name__)
default = object()

class EnvironProxy(property):
    """ Proxy attribute lookups to keys in the environ. """
    def __init__(self, name, factory=default):
        """
        An entry will be proxied to the supplied name in the .environ
        object of the property holder. A factory can be supplied, for
        values that need to be preinstantiated. If given as first
        parameter name is taken from the callable too.

        @param name: key (or factory for convenience)
        @param factory: literal object or callable
        """
        if not isinstance(name, basestring):
            factory = name
            name = factory.__name__
        self.name = name
        self.full_name = 'moin.%s' % name
        self.factory = factory
        property.__init__(self, self.get, self.set, self.delete)

    def get(self, obj):
        logging.debug("GET: '%s' on '%r'", self.name, obj)
        if self.full_name in obj.environ:
            res = obj.environ[self.full_name]
        else:
            factory = self.factory
            if factory is default:
                raise AttributeError(self.name)
            elif hasattr(factory, '__call__'):
                res = obj.environ.setdefault(self.full_name, factory(obj))
            else:
                res = obj.environ.setdefault(self.full_name, factory)
        return res

    def set(self, obj, value):
        logging.debug("SET: '%s' on '%r' to '%r'", self.name, obj, value)
        obj.environ[self.full_name] = value

    def delete(self, obj):
        logging.debug("DEL: '%s' on '%r'", self.name, obj)
        del obj.environ[self.full_name]

    def __repr__(self):
        return "<%s for '%s'>" % (self.__class__.__name__,
                                  self.full_name)

class Context(object):
    """ Standard implementation for the context interface.

    This one wraps up a Moin-Request object and the associated
    environ and also keeps track of it's changes.
    """
    def __init__(self, request):
        assert isinstance(request, Request)

        self.request = request
        self.environ = environ = request.environ
        self.personalities = self.environ.setdefault(
            'context.personalities', []
        )
        self.personalities.append(self.__class__.__name__)

    def become(self, cls):
        """ Become another context, based on given class.

        @param cls: class to change to, must be a sister class
        @rtype: boolean
        @return: wether a class change took place
        """
        if self.__class__ is cls:
            return False
        else:
            self.personalities.append(cls)
            self.__class__ = cls
            return True

    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.personalities)

class UserMixin(object):
    """ Mixin for user attributes and methods. """
    def user(self):
        return user.User(self, auth_method='request:invalid')
    user = EnvironProxy(user)

class LanguageMixin(object):
    """ Mixin for language attributes and methods. """
    lang = EnvironProxy('lang')

    def getText(self):
        lang = self.lang
        def _(text, i18n=i18n, request=self, lang=lang, **kw):
            return i18n.getText(text, request, lang, **kw)
        return _

    getText = property(getText)
    _ = getText

    def content_lang(self):
        return self.cfg.language_default
    content_lang = EnvironProxy(content_lang)
    current_lang = EnvironProxy('current_lang')

    def setContentLanguage(self, lang):
        """ Set the content language, used for the content div

        Actions that generate content in the user language, like search,
        should set the content direction to the user language before they
        call send_title!
        """
        self.content_lang = lang
        self.current_lang = lang


class HTTPMixin(object):
    """ Mixin for HTTP attributes and methods. """
    forbidden = EnvironProxy('old.forbidden', 0)
    session = EnvironProxy('session')

    _auth_redirected = EnvironProxy('old._auth_redirected', 0)
    cacheable = EnvironProxy('old.cacheable', 0)

    class _proxy(property):
        def __init__(self, name):
            self.name = name
            property.__init__(self, self.get, self.set, self.delete)
        def get(self, obj):
            return getattr(obj.request, self.name)
        def set(self, obj, value):
            setattr(obj.request, self.name, value)
        def delete(self, obj):
            delattr(obj.request, self.name)

    mimetype = _proxy('mimetype')
    content_type = _proxy('content_type')
    status = _proxy('status')
    status_code = _proxy('status_code')

    del _proxy

    def write(self, *data):
        if len(data) > 1:
            logging.warning("Some code still uses write with multiple arguments, "
                            "consider changing this soon")
        self.request.stream.writelines(data)

    # implementation of methods expected by RequestBase
    def send_file(self, fileobj, bufsize=8192, do_flush=None):
        def simple_wrapper(fileobj, bufsize):
            return iter(lambda: fileobj.read(bufsize), '')
        file_wrapper = self.environ.get('wsgi.file_wrapper', simple_wrapper)
        self.request.response = file_wrapper(fileobj, bufsize)
        raise MoinMoinFinish('sent file')

    def read(self, n=None):
        if n is None:
            return self.request.in_data
        else:
            return self.request.input_stream.read(n)

    def makeForbidden(self, resultcode, msg):
        status = {401: Unauthorized,
                  403: Forbidden,
                  404: NotFound,
                  503: SurgeProtection}
        raise status[resultcode](msg)

    def setHttpHeader(self, header):
        header, value = header.split(':', 1)
        self.headers.add(header, value)

    def disableHttpCaching(self, level=1):
        if level == 1 and self.headers.get('Pragma') == 'no-cache':
            return

        if level == 1:
            self.headers.set('Cache-Control', 'private, must-revalidate, mag-age=10')
        elif level == 2:
            self.headers.set('Cache-Control', 'no-cache')
            self.headers.set('Pragma', 'no-cache')
        self.request.expires = time.time() - 3600 * 24 * 365

    def http_redirect(self, url):
        """ Raise a simple redirect exception. """
        abort(redirect(url))

    def isSpiderAgent(self):
        return check_spider(self.request.user_agent, self.cfg)
    isSpiderAgent = EnvironProxy(isSpiderAgent)

class ActionMixin(object):
    """ Mixin for the action related attributes. """
    def action(self):
        return self.request.values.get('action', 'show')
    action = EnvironProxy(action)

    def rev(self):
        try:
            return int(self.values['rev'])
        except:
            return None
    rev = EnvironProxy(rev)

class ConfigMixin(object):
    """ Mixin for the everneeded config object. """
    def cfg(self):
        try:
            self.clock.start('load_multi_cfg')
            cfg = multiconfig.getConfig(self.request.url)
            self.clock.stop('load_multi_cfg')
            return cfg
        except error.NoConfigMatchedError:
            raise NotFound('<p>No wiki configuration matching the URL found!</p>')
    cfg = EnvironProxy(cfg)

class FormatterMixin(object):
    """ Mixin for the standard formatter attributes. """
    def html_formatter(self):
        return text_html.Formatter(self)
    html_formatter = EnvironProxy(html_formatter)

    def formatter(self):
        return self.html_formatter
    formatter = EnvironProxy(formatter)

class PageMixin(object):
    """ Mixin for ondemand rootpage. """
    page = EnvironProxy('page', None)
    def rootpage(self):
        from MoinMoin.Page import RootPage
        return RootPage(self)
    rootpage = EnvironProxy(rootpage)

class AuxilaryMixin(object):
    """
    Mixin for diverse attributes and methods that aren't clearly assignable
    to a particular phase of the request.
    """
    _fmt_hd_counters = EnvironProxy('_fmt_hd_counters')
    parsePageLinks_running = EnvironProxy('parsePageLinks_running', lambda o: {})
    mode_getpagelinks = EnvironProxy('mode_getpagelinks', 0)
    clock = EnvironProxy('clock', lambda o: Clock())
    pragma = EnvironProxy('pragma', lambda o: {})
    _login_messages = EnvironProxy('_login_messages', lambda o: [])
    _login_multistage = EnvironProxy('_login_multistage', None)
    _setuid_real_user = EnvironProxy('_setuid_real_user', None)
    pages = EnvironProxy('pages', lambda o: {})

    def uid_generator(self):
        pagename = None
        if hasattr(self, 'page') and hasattr(self.page, 'page_name'):
            pagename = self.page.page_name
        return UniqueIDGenerator(pagename=pagename)
    uid_generator = EnvironProxy(uid_generator)

    def dicts(self):
        """ Lazy initialize the dicts on the first access """
        from MoinMoin import wikidicts
        dicts = wikidicts.GroupDict(self)
        dicts.load_dicts()
        return dicts
    dicts = EnvironProxy(dicts)

    def reset(self):
        self.current_lang = self.cfg.language_default
        if hasattr(self, '_fmt_hd_counters'):
            del self._fmt_hd_counters
        if hasattr(self, 'uid_generator'):
            del self.uid_generator

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

class ThemeMixin(object):
    """ Mixin for the theme attributes and methods. """
    def _theme(self):
        self.initTheme()
        return self.theme
    theme = EnvironProxy('theme', _theme)

    def initTheme(self):
        """ Set theme - forced theme, user theme or wiki default """
        if self.cfg.theme_force:
            theme_name = self.cfg.theme_default
        else:
            theme_name = self.user.theme_name
        load_theme_fallback(self, theme_name)

class RedirectMixin(object):
    """ Mixin to redirect output into buffers instead to the client. """
    writestack = EnvironProxy('old.writestack', lambda o: list())

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

class HTTPContext(Context, HTTPMixin, ConfigMixin, UserMixin,
                  LanguageMixin, AuxilaryMixin):
    """ Context to act mainly in HTTP handling related phases. """
    def __getattr__(self, name):
        try:
            return getattr(self.request, name)
        except AttributeError, e:
            return super(HTTPContext, self).__getattribute__(name)

class RenderContext(Context, RedirectMixin, ConfigMixin, UserMixin,
                    LanguageMixin, ThemeMixin, AuxilaryMixin,
                    ActionMixin, PageMixin, FormatterMixin):
    """ Context to act during the rendering phase. """
    def write(self, *data):
        if len(data) > 1:
            logging.warning("Some code still uses write with multiple arguments, "
                            "consider changing this soon")
        self.request.stream.writelines(data)

# TODO: extend xmlrpc context
class XMLRPCContext(HTTPContext, PageMixin):
    """ Context to act during a XMLRPC request. """

class AllContext(HTTPContext, RenderContext):
    """ Catchall context to be able to quickly test old Moin code. """

class ScriptContext(AllContext):
    """ Context to act in scripting environments (e.g. former request_cli).

    For input, sys.stdin is used as 'wsgi.input', output is written directly
    to sys.stdout though.
    """
    def __init__(self, url='CLI', pagename=''):
        environ = create_environ()
        environ['HTTP_USER_AGENT'] = 'CLI/Script'
        environ['wsgi.input'] = sys.stdin
        request = Request(environ)
        super(ScriptContext, self).__init__(request)
        from MoinMoin import wsgiapp
        wsgiapp.init(self)
        request.url = url

    def write(self, *data):
        if len(data) > 1:
            logging.warning("Some code still uses write with multiple arguments, "
                            "consider changing this soon")
        for d in data:
            if isinstance(d, unicode):
                d = d.encode(config.charset)
            else:
                d = str(d)
            sys.stdout.write(d)
