# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI application

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from werkzeug.utils import responder
from werkzeug.wrappers import Response
from werkzeug.exceptions import NotFound

from MoinMoin.web.contexts import HTTPContext
from MoinMoin.web.utils import check_spider, handle_auth_form

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil, user, caching, error
from MoinMoin.action import get_names, get_available_actions
from MoinMoin.config import multiconfig
from MoinMoin.support.python_compatibility import set
from MoinMoin.util import IsWin9x
from MoinMoin.util.clock import Clock
from MoinMoin import auth

def _request_init(request):
    request.clock = Clock()
    request.clock.start('total')
    request.clock.start('base__init__')

    try:
        request.clock.start('load_multi_cfg')
        request.cfg = multiconfig.getConfig(request.url)
        request.clock.stop('load_multi_cfg')
    except error.NoConfigMatchedError:
        raise NotFound('<p>No wiki configuration matching the URL found!</p>')
    
    request.isSpiderAgent = check_spider(request.user_agent, request.cfg)
    
    request.action = request.form.get('action', 'show')
    
    try:
        request.rev = int(request.form['rev'])
    except:
        request.rev = None

    from MoinMoin.Page import RootPage
    request.rootpage = RootPage(request)

    from MoinMoin.logfile import editlog
    request.editlog = editlog.EditLog(request)

    from MoinMoin import i18n
    request.i18n = i18n
    i18n.i18n_init(request)

    lang = i18n.requestLanguage(request, try_user=False)
    request.getText = lambda text, i18n=i18n, request=request, lang=lang, **kw: i18n.getText(text, request, lang, **kw)
    
    user_obj = request.cfg.session_handler.start(request, request.cfg.session_id_handler)
    
    request.user = None
    request.user = handle_auth_form(user_obj)

    request.cfg.session_handler.after_auth(request, request.cfg.session_id_handler, request.user)

    if not request.user:
        request.user = user.User(request, auth_method='request:invalid')

    if 'setuid' in request.session and request.user.isSuperUser():
        request._setuid_real_user = request.user
        uid = request.session['setuid']
        request.user = user.User(request, uid, auth_method='setuid')
        request.user.valid = True

    if request.action != 'xmlrpc':
        if not request.forbidden and request.isForbidden():
            raise Forbidden()
        if not request.forbidden and request.surge_protect():
            raise SurgeProtection(retry_after=request.cfg.surge_lockout_time)

    request.pragma = {}
    request.mode_getpagelinks = 0 # is > 0 as long as we are in a getPageLinks call
    request.parsePageLinks_running = {} # avoid infinite recursion by remembering what we are already running

    request.lang = i18n.requestLanguage(request)
            # Language for content. Page content should use the wiki default lang,
            # but generated content like search results should use the user language.
    request.content_lang = request.cfg.language_default
    request.getText = lambda text, i18n=request.i18n, request=request, lang=request.lang, **kv: i18n.getText(text, request, lang, **kv)

    request.reset()

    from MoinMoin.formatter.text_html import Formatter
    request.html_formatter = Formatter(request)
    request.formatter = request.html_formatter

    request.clock.stop('base__init__')    

def application(environ, start_response):
    request = HTTPContext(environ)
    _request_init(request)
    request.run()

    response = Response(status=request.status,
                        headers=request.headers)

    if getattr(request, '_send_file', None) is not None:
        # moin wants to send a file (e.g. AttachFile.do_get)
        def simple_wrapper(fileobj, bufsize):
            return iter(lambda: fileobj.read(bufsize), '')
        file_wrapper = environ.get('wsgi.file_wrapper', simple_wrapper)
        response.response = file_wrapper(request._send_file, request._send_bufsize)
    else:
        response.response = request.output()
    return response

application = responder(application)
