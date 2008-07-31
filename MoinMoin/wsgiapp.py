# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - WSGI application

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from werkzeug.http import HeaderSet
from werkzeug.exceptions import HTTPException

from MoinMoin.web.contexts import AllContext, Context, XMLRPCContext
from MoinMoin.web.request import Request, MoinMoinFinish
from MoinMoin.web.utils import check_forbidden, check_setuid, check_surge_protect

from MoinMoin.Page import Page
from MoinMoin import auth, i18n, user, wikiutil, xmlrpc
from MoinMoin.action import get_names, get_available_actions

from MoinMoin import log
logging = log.getLogger(__name__)

def init(request):
    """
    Wraps an incoming WSGI request in a Context object and initializes
    several important attributes.
    """
    if isinstance(request, Context):
        context, request = request, request.request
    else:
        context = AllContext(request)
    context.clock.start('total')
    context.clock.start('init')

    context.lang = setup_i18n_preauth(context)

    context.session = context.cfg.session_service.get_session(request)

    userobj = setup_user(context, context.session)
    userobj, olduser = check_setuid(context, userobj)

    if not userobj:
        userobj = user.User(context, auth_method='request:invalid')

    context.user = userobj
    context._setuid_realuser = olduser

    context.lang = setup_i18n_postauth(context)

    context.reset()

    context.clock.stop('init')
    return context

def run(context):
    """ Run a context trough the application. """
    context.clock.start('run')
    request = context.request

    # preliminary access checks (forbidden, bots, surge protection)
    try:
        check_forbidden(context)
        check_surge_protect(context)

        action_name = context.action

        # handle XMLRPC calls
        if action_name == 'xmlrpc':
            response = xmlrpc.xmlrpc(XMLRPCContext(request))
        elif action_name == 'xmlrpc2':
            response = xmlrpc.xmlrpc2(XMLRPCContext(request))
        else:
            response = dispatch(request, context, action_name)
        context.cfg.session_service.finalize(context, context.session)
        return response
    except MoinMoinFinish:
        return request
    finally:
        context.clock.stop('run')

def remove_prefix(path, prefix=None):
    """ Remove an url prefix from the path info and return shortened path. """
    # we can have all action URLs like this: /action/ActionName/PageName?action=ActionName&...
    # this is just for robots.txt being able to forbid them for crawlers
    if prefix is not None:
        prefix = '/%s/' % prefix # e.g. '/action/'
        if path.startswith(prefix):
            # remove prefix and action name
            path = path[len(prefix):]
            action, path = (path.split('/', 1) + ['', ''])[:2]
            path = '/' + path
    return path

def dispatch(request, context, action_name='show'):
    cfg = context.cfg

    # The last component in path_info is the page name, if any
    path = remove_prefix(request.path, cfg.url_prefix_action)

    if path.startswith('/'):
        pagename = wikiutil.normalize_pagename(path, cfg)
    else:
        pagename = None

    # need to inform caches that content changes based on:
    # * cookie (even if we aren't sending one now)
    # * User-Agent (because a bot might be denied and get no content)
    # * Accept-Language (except if moin is told to ignore browser language)
    hs = HeaderSet(('Cookie', 'User-Agent'))
    if not cfg.language_ignore_browser:
        hs.add('Accept-Language')
    request.headers.add('Vary', str(hs))

    # Handle request. We have these options:
    # 1. jump to page where user left off
    if not pagename and context.user.remember_last_visit and action_name == 'show':
        response = handle_last_visit(context)
    # 2. handle action
    else:
        response = handle_action(context, pagename, action_name)
    if isinstance(response, Context):
        response = response.request
    return response

def handle_action(context, pagename, action_name='show'):
    """ Actual dispatcher function for non-XMLRPC actions.

    Also sets up the Page object for this request, normalizes and
    redirects to canonical pagenames and checks for non-allowed
    actions.
    """
    _ = context.getText
    cfg = context.cfg

    # pagename could be empty after normalization e.g. '///' -> ''
    # Use localized FrontPage if pagename is empty
    if not pagename:
        context.page = wikiutil.getFrontPage(context)
    else:
        context.page = Page(context, pagename)
        if '_' in pagename and not context.page.exists():
            pagename = pagename.replace('_', ' ')
            page = Page(context, pagename)
            if page.exists():
                url = page.url(context)
                return abort(redirect(url))

    msg = None
    # Complain about unknown actions
    if not action_name in get_names(cfg):
        msg = _("Unknown action %(action_name)s.") % {
                'action_name': wikiutil.escape(action_name), }

    # Disallow non available actions
    elif action_name[0].isupper() and not action_name in \
            get_available_actions(cfg, context.page, context.user):
        msg = _("You are not allowed to do %(action_name)s on this page.") % {
                'action_name': wikiutil.escape(action_name), }
        if not context.user.valid:
            # Suggest non valid user to login
            msg += " " + _("Login and try again.")

    if msg:
        context.theme.add_msg(msg, "error")
        context.page.send_page()
    # Try action
    else:
        from MoinMoin import action
        handler = action.getHandler(cfg, action_name)
        if handler is None:
            msg = _("You are not allowed to do %(action_name)s on this page.") % {
                    'action_name': wikiutil.escape(action_name), }
            if not context.user.valid:
                # Suggest non valid user to login
                msg += " " + _("Login and try again.")
            context.theme.add_msg(msg, "error")
            context.page.send_page()
        else:
            handler(context.page.page_name, context)

    return context

def setup_user(context, session):
    """ Try to retrieve a valid user object from the request, be it
    either through the session or through a login. """
    # first try setting up from session
    userobj = auth.setup_from_session(context, session)

    # then handle login/logout forms
    form = context.request.values

    if 'login' in form:
        params = {
            'username': form.get('name'),
            'password': form.get('password'),
            'attended': True,
            'openid_identifier': form.get('openid_identifier'),
            'stage': form.get('stage')
        }
        userobj = auth.handle_login(context, userobj, **params)
    elif 'logout' in form:
        userobj = auth.handle_logout(context, userobj)
    else:
        userobj = auth.handle_request(context, userobj)

    return userobj

def setup_i18n_preauth(context):
    """ Determine language for the request in absence of any user info. """
    if i18n.languages is None:
        i18n.i18n_init(context)

    cfg = context.cfg
    lang = None
    if i18n.languages and not cfg.language_ignore_browser:
        for l in context.request.accept_languages:
            if l in i18n.languages:
                lang = l
                break
    if lang is None and cfg.language_default in i18n.languages:
        lang = cfg.language_default
    else:
        lang = 'en'
    return lang

def setup_i18n_postauth(context):
    """ Determine language for the request after user-id is established. """
    user = context.user
    if user and user.valid and user.language:
        return user.language
    else:
        return context.lang

def handle_last_visit(request, context):
    """ Redirect to last visited page (or frontpage) on missing pagename. """
    pagetrail = context.user.getTrail()
    if pagetrail:
        # Redirect to last page visited
        last_visited = pagetrail[-1]
        wikiname, pagename = wikiutil.split_interwiki(last_visited)
        if wikiname != 'Self':
            wikitag, wikiurl, wikitail, error = wikiutil.resolve_interwiki(context, wikiname, pagename)
            url = wikiurl + wikiutil.quoteWikinameURL(wikitail)
        else:
            url = Page(context, pagename).url(context)
    else:
        # Or to localized FrontPage
        url = wikiutil.getFrontPage(context).url(context)
    return abort(redirect(url))

def application(environ, start_response):
    try:
        request = Request(environ)
        context = init(request)
        response = run(context)
    except HTTPException, e:
        response = e

    context.clock.stop('total')
    return response(environ, start_response)

class ProxyTrust(object):
    def __init__(self, app, proxies):
        self.app = app
        self.proxies = proxies

    def __call__(environ, start_response):
        if 'HTTP_X_FORWARDED_FOR' in environ:
            addrs = environ.pop('HTTP_X_FORWARDED_FOR').split(',')
            addrs = [x.strip() for addr in addrs]
        elif 'REMOTE_ADDR' in environ:
            addrs = [environ['REMOTE_ADDR']]
        else:
            addrs = [None]
        result = [addr for addr in addrs if addr not in self.proxies]
        if result:
            environ['REMOTE_ADDR'] = result[-1]
        elif addrs[-1] is not None:
            environ['REMOTE_ADDR'] = addrs[-1]
        else:
            del environ['REMOTE_ADDR']
        return self.app(environ, start_response)

def run_server(config):
    from os import path
    from MoinMoin.config import url_prefix_static
    from MoinMoin.web.serving import RequestHandler
    from werkzeug.serving import run_simple
    from werkzeug.utils import SharedDataMiddleware

    shared = {url_prefix_static: config.docs,
              '/favicon.ico': path.join(config.docs, 'favicon.ico'),
              '/robots.txt': path.join(config.docs, 'robots.txt')}

    app = SharedDataMiddleware(application, shared)

    params = {}
    params['use_debugger'] = config.debug
    params['threaded'] = True
    params['request_handler'] = RequestHandler

    run_simple(config.interface, config.port, app, **params)
