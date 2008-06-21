# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Utility functions for the web-layer

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""
import time

from werkzeug.exceptions import abort
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

def check_setuid(request):
    """ Check for setuid conditions and set user accordingly
    
    @param request: a moin request object
    @rtype: boolean
    @return: Wether a UID change took place
    """
    if 'setuid' in request.session and request.user.isSuperUser():
        request._setuid_real_user = request.user
        uid = request.session['setuid']
        request.user = user.User(request, uid, auth_method='setuid')
        request.user.valid = True
        return True
    else:
        return False

def check_forbidden(request):
    """ Simple action and host access checks

    Spider agents are checked against the called actions,
    hosts against the blacklist. Raises Forbidden if triggered.
    """
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
    """ Check for excessive requests

    Raises a SurgeProtection exception on wiki overuse.

    @param request: a moin request object
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

def handle_auth(user_obj, request, attended=False, username=None,
                password=None, openid_identifier=None, login=None,
                logout=None, stage=None):
    extra = { 'cookie': request.cookies }
    if login:
        extra['attended'] = attended
        extra['username'] = username
        extra['password'] = password
        extra['openid_identifier'] = openid_identifier
        if stage:
            extra['multistage'] = True
    login_msgs = []
    request._login_multistage = None

    if logout and 'setuid' in request.session:
        del request.session['setuid']
        return user_obj

    for authmethod in request.cfg.auth:
        if logout:
            user_obj, cont = authmethod.logout(request, user_obj, **extra)
        elif login:
            if stage and authmethod.name != stage:
                continue
            ret = authmethod.login(request, user_obj, **extra)
            user_obj = ret.user_obj
            cont = ret.continue_flag
            if stage:
                stage = None
                del extra['multistage']
            if ret.multistage:
                request._login_multistage = ret.multistage
                request._login_multistage_name = authmethod.name
                return user_obj
            if ret.redirect_to:
                nextstage = auth.get_multistage_continuation_url(request, authmethod.name)
                url = ret.redirect_to
                url = url.replace('%return_form', quote_plus(nextstage))
                url = url.replace('%return', quote(nextstage))
                abort(redirect(url))
            msg = ret.message
            if msg and not msg in login_msgs:
                login_msgs.append(msg)
        else:
            user_obj, cont = authmethod.request(request, user_obj, **extra)
        if not cont:
            break

    request._login_messages = login_msgs
    return user_obj

def handle_auth_form(user_obj, request):
    form = request.form
    params = {
        'username': form.get('name'),
        'password': form.get('password'),
        'openid_identifier': form.get('openid_identifier'),
        'login': 'login' in form,
        'logout': 'logout' in form,
        'stage': form.get('stage'),
        'attended': True
    }
    return handle_auth(user_obj, request, **params)

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
    return abort(redirect(url))

class UniqueIDGenerator(object):
    def __init__(self, pagename=None):
        self.unique_stack = []
        self.include_stack = []
        self.include_id = None
        self.page_ids = {None: {}}
        self.pagename = pagename

    def push(self):
        """
        Used by the TOC macro, this ensures that the ID namespaces
        are reset to the status when the current include started.
        This guarantees that doing the ID enumeration twice results
        in the same results, on any level.
        """
        self.unique_stack.append((self.page_ids, self.include_id))
        self.include_id, pids = self.include_stack[-1]
        self.page_ids = {}
        for namespace in pids:
            self.page_ids[namespace] = pids[namespace].copy()

    def pop(self):
        """
        Used by the TOC macro to reset the ID namespaces after
        having parsed the page for TOC generation and after
        printing the TOC.
        """
        self.page_ids, self.include_id = self.unique_stack.pop()
        return self.page_ids, self.include_id

    def begin(self, base):
        """
        Called by the formatter when a document begins, which means
        that include causing nested documents gives us an include
        stack in self.include_id_stack.
        """
        pids = {}
        for namespace in self.page_ids:
            pids[namespace] = self.page_ids[namespace].copy()
        self.include_stack.append((self.include_id, pids))
        self.include_id = self(base)
        # if it's the page name then set it to None so we don't
        # prepend anything to IDs, but otherwise keep it.
        if self.pagename and self.pagename == self.include_id:
            self.include_id = None

    def end(self):
        """
        Called by the formatter when a document ends, restores
        the current include ID to the previous one and discards
        the page IDs state we kept around for push().
        """
        self.include_id, pids = self.include_stack.pop()

    def __call__(self, base, namespace=None):
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
        if not namespace in self.page_ids:
            self.page_ids[namespace] = {}
        count = self.page_ids[namespace].get(base, -1) + 1
        self.page_ids[namespace][base] = count
        if not count:
            return base
        return u'%s-%d' % (base, count)        
