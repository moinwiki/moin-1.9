# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Utility functions for the web-layer

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
from werkzeug.utils import redirect

from MoinMoin import log
from MoinMoin import wikiutil
from MoinMoin.Page import Page

logging = log.getLogger(__name__)

def check_spider(useragent, cfg):
    """ Simple check if useragent is a spider bot
    
    @param useragent: werkzeug.useragents.UserAgent
    @param cfg: wikiconfig instance
    """
    is_spider = False
    if useragent and cfg.cache.ua_spiders:
        is_spider = cfg.cache.ua_spiders.search(useragent.browser) is not None
    return is_spider

def handle_auth(user_obj, **kw):
    logging.warning("handle_auth still needs implementation")
    return user_obj

def handle_auth_form(user_obj, form):
    username = form.get('name')
    password = form.get('password')
    openid_identifier = form.get('openid_identifier')
    login = 'login' in form
    logout = 'logout' in form
    stage = form.get('stage')
    attended = True
    return handle_auth(user_obj, **locals())

def redirect_last_visited(request):
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
    url = request.getQualifiedURL(url)
    return redirect(url)
