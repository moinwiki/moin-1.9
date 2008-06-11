# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Utility functions for the web-layer

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import time

from werkzeug.utils import redirect

from MoinMoin import log
from MoinMoin import wikiutil
from MoinMoin.Page import Page
from MoinMoin.web.exceptions import Forbidden, SurgeProtection

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

def check_forbidden(request):
    args = request.args
    action = args.get('action')
    if ((args or request.method != 'GET') and
        action not in ['rss_rc', 'show', 'sitemap'] and
        not (action == 'AttachFile' and args.get('do') == 'get')):
        if check_spider(request.user_agent, request.cfg):
            raise Forbidden()
    if request.cfg.hosts_deny:
        remote_addr = request.remote_addr
        for host in request.cfg.hosts_deny:
            if host[-1] == '.' and remote_addr.startswith(host):
                logging.debug("hosts_deny (net): %s" % str(forbidden))
                raise Forbidden()
            if remote_addr == host:
                logging.debug("hosts_deny (ip): %s" % str(forbidden))
                raise Forbidden()
    return False

def check_surge_protect(request, kick=False):
    """ check if someone requesting too much from us,
        if kick_him is True, we unconditionally blacklist the current user/ip
    """
    limits = request.cfg.surge_action_limits
    if not limits:
        return False

    validuser = request.user.valid
    current_id = validuser and request.user.name or request.remote_addr
    if not validuser and current_id.startswith('127.'): # localnet
        return False
    current_action = request.action

    default_limit = request.cfg.surge_action_limits.get('default', (30, 60))

    now = int(time.time())
    surgedict = {}
    surge_detected = False

    try:
        # if we have common farm users, we could also use scope='farm':
        cache = caching.CacheEntry(request, 'surgeprotect', 'surge-log', scope='wiki', use_encode=True)
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
                timestamps.append((now + request.cfg.surge_lockout_time, surge_indicator)) # continue like that and get locked out

        if current_action != 'AttachFile': # don't add AttachFile accesses to all or picture galleries will trigger SP
            current_action = 'all' # put a total limit on user's requests
            maxnum, dt = limits.get(current_action, default_limit)
            events = surgedict.setdefault(current_id, {})
            timestamps = events.setdefault(current_action, [])

            if kick_him: # ban this guy, NOW
                timestamps.extend([(now + request.cfg.surge_lockout_time, "!")] * (2 * maxnum))

            surge_detected = surge_detected or len(timestamps) > maxnum

            surge_indicator = surge_detected and "!" or ""
            timestamps.append((now, surge_indicator))
            if surge_detected:
                if len(timestamps) < maxnum * 2:
                    timestamps.append((now + request.cfg.surge_lockout_time, surge_indicator)) # continue like that and get locked out

        data = []
        for id, events in surgedict.items():
            for action, timestamps in events.items():
                for t, surge_indicator in timestamps:
                    data.append("%s\t%d\t%s\t%s" % (id, t, action, surge_indicator))
        data = "\n".join(data)
        cache.update(data)
    except StandardError:
        pass

    if surge_detected:
        raise SurgeProtection(retry_after=request.cfg.surge_lockout_time)
    else:
        return False

def handle_auth(user_obj, **kw):
    logging.warning("handle_auth still needs implementation")
    return user_obj

def handle_auth_form(user_obj, form):
    params = {
        'username': form.get('name'),
        'password': form.get('password'),
        'openid_identifier': form.get('openid_identifier'),
        'login': 'login' in form,
        'logout': 'logout' in form,
        'stage': form.get('stage'),
        'attended': True
    }
    return handle_auth(user_obj, **params)

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
