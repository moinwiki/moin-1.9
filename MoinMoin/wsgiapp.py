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

from MoinMoin.web.contexts import HTTPContext, RenderContext, AllContext
from MoinMoin.web.request import Request
from MoinMoin.web.utils import check_spider, check_forbidden, check_setuid
from MoinMoin.web.utils import check_surge_protect
from MoinMoin.web.apps import HTTPExceptionsMiddleware

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil, user, caching, error
from MoinMoin.action import get_names, get_available_actions
from MoinMoin.config import multiconfig
from MoinMoin.support.python_compatibility import set
from MoinMoin.util import IsWin9x
from MoinMoin.request import MoinMoinFinish, RemoteClosedConnection
from MoinMoin import auth

from MoinMoin import log
logging = log.getLogger(__name__)

def init(request):
    request = AllContext(request)
    request.clock.start('total')
    request.clock.start('base__init__')

    request.session = request.cfg.session_service.get_session(request)

    # auth & user handling
    userobj = None
    form = request.form

    if 'login' in form:
        params = {
            'username': form.get('name'),
            'password': form.get('password'),
            'attended': True,
            'openid_identifier': form.get('openid_identifier'),
            'stage': form.get('stage')
        }
        userobj = auth.handle_login(request, userobj, **params)
    elif 'logout' in form:
        userobj = auth.handle_logout(request, userobj)
    else:
        userobj = auth.handle_request(request, userobj)

    userobj, olduser = check_setuid(request, userobj)

    if not userobj:
        userobj = user.User(request, auth_method='request:invalid')

    request.user = userobj
    request._setuid_real_user = olduser

    # preliminary access control
    # check against spiders, blacklists and request-spam
    check_forbidden(request)
    check_surge_protect(request)

    request.reset()

    request.clock.stop('base__init__')
    return request

def run(request):
    
    _ = request.getText
    request.clock.start('run')

    request.initTheme()

    action_name = request.action
    if request.cfg.log_timing:
        request.timing_log(True, action_name)

    # parse request data
    try:
        # The last component in path_info is the page name, if any
        path = request.path

        # we can have all action URLs like this: /action/ActionName/PageName?action=ActionName&...
        # this is just for robots.txt being able to forbid them for crawlers
        prefix = request.cfg.url_prefix_action
        if prefix is not None:
            prefix = '/%s/' % prefix # e.g. '/action/'
            if path.startswith(prefix):
                # remove prefix and action name
                path = path[len(prefix):]
                action, path = (path.split('/', 1) + ['', ''])[:2]
                path = '/' + path

        if path.startswith('/'):
            pagename = wikiutil.normalize_pagename(path, request.cfg)
        else:
            pagename = None

        # need to inform caches that content changes based on:
        # * cookie (even if we aren't sending one now)
        # * User-Agent (because a bot might be denied and get no content)
        # * Accept-Language (except if moin is told to ignore browser language)
        if request.cfg.language_ignore_browser:
            request.setHttpHeader("Vary: Cookie,User-Agent")
        else:
            request.setHttpHeader("Vary: Cookie,User-Agent,Accept-Language")

        # Handle request. We have these options:
        # 1. jump to page where user left off
        if not pagename and request.user.remember_last_visit and action_name == 'show':
            pagetrail = request.user.getTrail()
            if pagetrail:
                # Redirect to last page visited
                last_visited = pagetrail[-1]
                wikiname, pagename = wikiutil.split_interwiki(last_visited)
                if wikiname != 'Self':
                    wikitag, wikiurl, wikitail, error = wikiutil.resolve_interwiki(request, wikiname, pagename)
                    url = wikiurl + wikiutil.quoteWikinameURL(wikitail)
                else:
                    url = Page(request, pagename).url(request)
            else:
                # Or to localized FrontPage
                url = wikiutil.getFrontPage(request).url(request)
            return abort(redirect(url))

        # 2. handle action
        else:
            # pagename could be empty after normalization e.g. '///' -> ''
            # Use localized FrontPage if pagename is empty
            if not pagename:
                request.page = wikiutil.getFrontPage(request)
            else:
                request.page = Page(request, pagename)
                if '_' in pagename and not request.page.exists():
                    pagename = pagename.replace('_', ' ')
                    page = Page(request, pagename)
                    if page.exists():
                        url = page.url(request)
                        return abort(redirect(url))

            msg = None
            # Complain about unknown actions
            if not action_name in get_names(request.cfg):
                msg = _("Unknown action %(action_name)s.") % {
                        'action_name': wikiutil.escape(action_name), }

            # Disallow non available actions
            elif action_name[0].isupper() and not action_name in request.getAvailableActions(request.page):
                msg = _("You are not allowed to do %(action_name)s on this page.") % {
                        'action_name': wikiutil.escape(action_name), }
                if not request.user.valid:
                    # Suggest non valid user to login
                    msg += " " + _("Login and try again.")

            if msg:
                request.theme.add_msg(msg, "error")
                request.page.send_page()
            # Try action
            else:
                from MoinMoin import action
                handler = action.getHandler(request, action_name)
                if handler is None:
                    msg = _("You are not allowed to do %(action_name)s on this page.") % {
                            'action_name': wikiutil.escape(action_name), }
                    if not request.user.valid:
                        # Suggest non valid user to login
                        msg += " " + _("Login and try again.")
                    request.theme.add_msg(msg, "error")
                    request.page.send_page()
                else:
                    handler(request.page.page_name, request)

        # every action that didn't use to raise MoinMoinFinish must call this now:
        # request.theme.send_closing_html()    

    except MoinMoinFinish:
        pass
    except RemoteClosedConnection:
        # at least clean up
        pass
    except SystemExit:
        raise # fcgi uses this to terminate a thread

    if request.cfg.log_timing:
        request.timing_log(False, action_name)

        #return request.finish()
    request.cfg.session_service.finalize(request, request.session)
    return request

def application(request):
    run(init(request))

    if getattr(request, '_send_file', None) is not None:
        # moin wants to send a file (e.g. AttachFile.do_get)
        def simple_wrapper(fileobj, bufsize):
            return iter(lambda: fileobj.read(bufsize), '')
        file_wrapper = request.environ.get('wsgi.file_wrapper', simple_wrapper)
        request.response = file_wrapper(request._send_file, request._send_bufsize)
    return request

application = Request.application(application)
application = HTTPExceptionsMiddleware(application)
