# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - modular authentication and session code

    Here are some methods moin can use in cfg.auth authentication method list.
    The methods from that list get called (from request.py) in that sequence.
    They get request as first argument and also some more kw arguments:
       name: the value we did get from a POST of the UserPreferences page
             in the "name" form field (or None)
       password: the value of the password form field (or None)
       login: True if user has clicked on Login button
       logout: True if user has clicked on Logout button
       user_obj: the user_obj we have until now (user_obj returned from
                 previous auth method or None for first auth method)
       cookie: a Cookie.SimpleCookie instance containing the cookies for
               this request, or None if no (valid) cookies were set
       (we maybe add some more here)

    Use code like this to get them:
        name = kw.get('name') or ''
        password = kw.get('password') or ''
        login = kw.get('login')
        logout = kw.get('logout')
        cookie = kw.get('cookie')
        request.log("got name=%s len(password)=%d login=%r logout=%r" % (name, len(password), login, logout))
    
    The called auth method then must return a tuple (user_obj, continue_flag).
    user_obj can be one of:
    * a (newly created) User object
    * None if we want to inhibit log in from previous auth methods
    * what we got as kw argument user_obj (meaning: no change).
    continue_flag is a boolean indication whether the auth loop shall continue
    trying other auth methods (or not).

    The methods give a kw arg "auth_attribs" to User.__init__ that tells
    which user attribute names are DETERMINED and set by this auth method and
    must not get changed by the user using the UserPreferences form.
    It also gives a kw arg "auth_method" that tells the name of the auth
    method that authentified the user.

    The moin_session method also defines request.session for both logged-in
    as well as not logged-in users.

    @copyright: 2005-2006 Bastian Blank, Florian Festi, MoinMoin:ThomasWaldmann,
                          MoinMoin:AlexanderSchremmer, Nick Phillips,
                          MoinMoin:FrankieChow, MoinMoin:NirSoffer
    @copyright: 2007      MoinMoin:JohannesBerg

    @license: GNU GPL, see COPYING for details.
"""

import time, Cookie
from MoinMoin import user
from MoinMoin.caching import CacheEntry

# cookie names
MOIN_SESSION = 'MOIN_SESSION'

# maximum number of stored secrets, i.e. maximum number of
# different machines a user can use concurrently without having
# to log in again
MAX_STORED_SECRETS = 20

import hmac, random
from sha import sha

class UserSecurityStringCache:
    """UserSecurityStringCache -- cache a list of secrets for user cookies

    In order to avoid cookie stealing even after a user has logged out we
    keep a list of secrets (in the cache) associated with a user and verify
    that the cookie matches the right one.

    This class manages the secrets and their LRU expiry.
    """
    def __init__(self, request, userid):
        # we use 'farm' scope but hash the user_dir into the
        # secret cache name to make both shared and non-shared
        # user_dir in a farm work properly
        cache_name = sha(userid + request.cfg.user_dir).hexdigest()
        self.ce = CacheEntry(request, 'ussc', cache_name, 'farm', use_pickle=True)

    def _get(self):
        """Internal: get string dict and LRU list from cache"""
        if self.ce.exists():
            return self.ce.content()
        return {}, []

    def update(self, secidx):
        """ tell the secret string cache that the secret identified
            was used

        @param secidx: the index of that secret or None if a new one
                       shall be assigned
        """
        secrets, lru = self._get()
        # just move this secret to the front of the LRU queue
        lru.remove(secidx)
        lru.insert(0, secidx)
        self.ce.update((secrets, lru))

    def insert(self, secstring):
        """ insert a new secret string into the cache

        @param secstring: the new secret string
        @rtype: int
        @return: the new secret index
        """
        secrets, lru = self._get()
        # find a new unused index
        # try one that we'll expire first
        if len(lru) >= MAX_STORED_SECRETS:
            secidx = lru[-1]
        else:
            # select an unused index
            secidx = random.randint(0, MAX_STORED_SECRETS*5)
            while secidx in lru:
                secidx = random.randint(0, MAX_STORED_SECRETS*5)
        for idx in lru[MAX_STORED_SECRETS-1:]:
            data = SessionData(secrets[idx])
            data.delete()
            del secrets[idx]
        lru = lru[:MAX_STORED_SECRETS-1]
        lru.insert(0, secidx)
        secrets[secidx] = secstring
        self.ce.update((secrets, lru))
        return secidx

    def remove(self, secidx):
        """ remove a given secret from the cache

        @param secidx: the index of the secret to be removed
        """
        secrets, lru = self._get()
        del secrets[secidx]
        lru = [idx for idx in lru if idx != secidx]
        self.ce.update((secrets,lru))

    def getsecret(self, secidx):
        secrets, lru = self._get()
        if secidx in secrets:
            return secrets[secidx]
        return ''

class SessionData:
    def __init__(self, request, name):
        # we can use farm scope since the session name is totally random
        # this means that the session is kept over multiple wikis in a farm
        # when they share user_dir and cookies
        self.ce = CacheEntry(request, 'session', name, 'farm', use_pickle=True)
        self.request = request
        if self.ce.exists():
            self._data = self.ce.content()
        else:
            self._data = {}

    def __setitem__(self, name, value):
        self._data[name] = value
        self.ce.update(self._data)

    def __getitem__(self, name):
        return self._data[name]

    def __contains__(self, name):
        return name in self._data

    def __delitem__(self, name):
        del self._data[name]
        if len(self._data) == 0:
            self.ce.remove()
        else:
            self.ce.update(self._data)

    def get(self, name, default):
        return self._data.get(name, default)

    def delete(self):
        if self.ce.exists():
            self.ce.remove()

    def rename(self, newname):
        self.ce.remove()
        self.ce = CacheEntry(self.request, 'session', newname, 'farm', use_pickle=True)
        if len(self._data):
            self.ce.update(self._data)


def generate_security_string(length):
    """ generate a random length (length/2 .. length) string with random content """
    random_length = random.randint(length/2, length)
    safe = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-'
    return ''.join([random.choice(safe) for i in range(random_length)])

def sign_cookie_data(request, data, securitystring):
    """ generate a hash string based the securitystring and the data.
    """
    return hmac.new(securitystring, data).hexdigest()

def makeCookie(request, cookie_name, cookie_string, maxage, expires):
    """ create an appropriate cookie """
    c = Cookie.SimpleCookie()
    cfg = request.cfg
    c[cookie_name] = cookie_string
    c[cookie_name]['max-age'] = maxage
    if cfg.cookie_domain:
        c[cookie_name]['domain'] = cfg.cookie_domain
    if cfg.cookie_path:
        c[cookie_name]['path'] = cfg.cookie_path
    else:
        path = request.getScriptname()
        if not path:
            path = '/'
        c[cookie_name]['path'] = path
    # Set expires for older clients
    c[cookie_name]['expires'] = request.httpDate(when=expires, rfc='850')
    return c.output()

def getCookieLifetime(request, u):
    """ Get cookie lifetime for the user object u
    """
    lifetime = int(request.cfg.cookie_lifetime) * 3600
    forever = 10 * 365 * 24 * 3600 # 10 years
    if not lifetime:
        return forever
    elif lifetime > 0:
        if u.remember_me:
            return forever
        return lifetime
    elif lifetime < 0:
        return -lifetime
    return lifetime

def setCookie(request, cookie_name, cookie_string, maxage, expires):
    """ Set cookie, raw helper.
    """
    cookie = makeCookie(request, cookie_name, cookie_string, maxage, expires)
    # Set cookie
    request.setHttpHeader(cookie)
    # IMPORTANT: Prevent caching of current page and cookie
    request.disableHttpCaching()

def setSessionCookie(request, u, secret=None, securitystringcache=None,
                     secidx=None, session=None):
    """ Set moin_session cookie for user obj u

    cfg.cookie_lifetime and the user 'remember_me' setting set the
    lifetime of the cookie. lifetime in in hours, see table:
    
    value   cookie lifetime
    ----------------------------------------------------------------
     = 0    forever, ignoring user 'remember_me' setting
     > 0    n hours, or forever if user checked 'remember_me'
     < 0    -n hours, ignoring user 'remember_me' setting
    """
    import base64
    maxage = getCookieLifetime(request, u)
    expires = time.time() + maxage
    enc_username = base64.encodestring(u.auth_username).replace('\n', '')
    enc_id = base64.encodestring(u.id).replace('\n', '')
    if secret is None and secidx is None:
        secret = generate_security_string(32)
    if securitystringcache is None:
        securitystringcache = UserSecurityStringCache(request, u.id)
    if secret is None:
        # secidx must be assigned
        securitystringcache.update(secidx)
        secret = securitystringcache.getsecret(secidx)
    else:
        secidx = securitystringcache.insert(secret)
    cookie_body = "username=%s:id=%s:expires=%d:secidx=%d" % (enc_username, enc_id, expires, secidx)
    cookie_hash = sign_cookie_data(request, cookie_body, secret)
    cookie_string = ':'.join([cookie_hash, cookie_body])
    setCookie(request, MOIN_SESSION, cookie_string, maxage, expires)

    # move session data to new identifier
    if session:
        session.rename(secret)
    else:
        session = SessionData(request, secret)
    request.session = session

def deleteCookie(request, cookie_name):
    """ Delete the user cookie by sending expired cookie with null value

    According to http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2109.html#sec-4.2.2
    Deleted cookie should have Max-Age=0. We also have expires attribute,
    which is probably needed for older browsers.

    Finally, delete the saved cookie and create a new user based on the new settings.
    """
    cookie_string = ''
    maxage = 0
    # Set expires to one year ago for older clients
    expires = time.time() - (3600 * 24 * 365) # 1 year ago
    cookie = makeCookie(request, cookie_name, cookie_string, maxage, expires)
    # Set cookie
    request.setHttpHeader(cookie)
    # IMPORTANT: Prevent caching of current page and cookie        
    request.disableHttpCaching()

def setAnonCookie(request, session_name):
    if not hasattr(request.cfg, 'anonymous_cookie_lifetime'):
        return
    request.session = SessionData(request, session_name)
    lifetime = request.cfg.anonymous_cookie_lifetime * 3600
    expires = time.time() + lifetime
    setCookie(request, MOIN_SESSION, session_name, lifetime, expires)


def moin_login(request, **kw):
    """ handle login from moin login form, session has to be established later by moin_session """
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    #logout = kw.get('logout')
    user_obj = kw.get('user_obj')

    cfg = request.cfg
    verbose = False
    if hasattr(cfg, 'moin_login_verbose'):
        verbose = cfg.moin_login_verbose

    #request.log("auth.moin_login: name=%s login=%r logout=%r user_obj=%r" % (username, login, logout, user_obj))

    if login:
        if verbose: request.log("moin_login performing login action")
        u = user.User(request, name=username, password=password, auth_method='moin_login')
        if u.valid:
            if verbose: request.log("moin_login got valid user...")
            user_obj = u
        else:
            if verbose: request.log("moin_login not valid, previous valid=%d." % user_obj.valid)

    return user_obj, True

def moin_session(request, **kw):
    """ Authenticate via cookie.
    
    We don't handle initial logins (except to set the appropriate cookie), just
    ongoing sessions, and logout. Use another method for initial login.
    """
    import base64

    username = kw.get('name')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')

    cfg = request.cfg
    verbose = False
    if hasattr(cfg, 'moin_session_verbose'):
        verbose = cfg.moin_session_verbose

    cookie_name = MOIN_SESSION

    # load up our cookie
    cookie = kw.get('cookie')
    if cookie is not None and cookie_name in cookie:
        cookievalue = cookie[cookie_name].value
        cookieitems = cookievalue.split(':', 1)
    else:
        cookievalue = None

    if verbose: request.log("auth.moin_session: name=%s login=%r logout=%r user_obj=%r" % (username, login, logout, user_obj))

    if login:
        if verbose: request.log("moin_session performing login action")

        # Has any other method successfully authenticated?
        if user_obj is not None and user_obj.valid:
            # Yes - set up session cookie
            if verbose: request.log("moin_session got valid user from previous auth method, setting cookie...")
            if verbose: request.log("moin_session got auth_username %s." % user_obj.auth_username)
            sessiondata = None
            if cookievalue and len(cookieitems) == 1:
                # we have an anonymous session so migrate the data
                sessiondata = SessionData(request, cookievalue)
            setSessionCookie(request, user_obj, session=sessiondata)
            return user_obj, True # we make continuing possible, e.g. for smbmount
        else:
            # No other method succeeded, so allow continuation...
            # XXX Cookie clear here???
            if verbose: request.log("moin_session did not get valid user from previous auth method, doing nothing")
            return user_obj, True

    if cookievalue is None:
        # No valid cookie
        if verbose: request.log("either no cookie or no %s key" % cookie_name)
        return user_obj, True

    if len(cookieitems) == 1:
        # non-logged in session
        setAnonCookie(request, cookieitems[0])
        return user_obj, True

    # otherwise we have a signed cookie
    cookie_hash, cookie_body = cookieitems

    # Parse cookie, be careful
    params = {'username': '', 'id': '', 'expires': 0, 'secidx': -1, }
    cookie_pairs = cookie_body.split(":")
    for key, value in [pair.split("=", 1) for pair in cookie_pairs]:
        try:
            if isinstance(params[key], str):
                params[key] = base64.decodestring(value)
            elif isinstance(params[key], int):
                params[key] = int(value)
        except Exception:
            # ignore any errors from parsing the values
            pass
    # This may seem odd, but checking expiry is cheaper
    # than checking the signature.
    if params['expires'] < time.time():
        # XXX Cookie clear here???
        if verbose: request.log("cookie expired")
        return user_obj, True

    secidx = params['secidx']

    ussc = UserSecurityStringCache(request, params['id'])
    secstring = ussc.getsecret(secidx)
    if cookie_hash != sign_cookie_data(request, cookie_body, secstring):
        # XXX Cookie clear here???
        if verbose: request.log("cookie recovered had invalid hash")
        return user_obj, True

    if verbose: request.log("Cookie OK, authenticated.")

    # use the security string as the session identifier now
    request.session = SessionData(request, secstring)

    # XXX Should name be in auth_attribs?
    u = user.User(request,
                  id=params['id'],
                  auth_username=params['username'],
                  auth_method='moin_session',
                  auth_attribs=(),
                  )

    if logout:
        if verbose: request.log("Logout requested, setting u invalid and 'deleting' cookie")
        u.valid = 0 # just make user invalid, but remember him
        # delete secret for this cookie
        ussc.remove(secidx)
        deleteCookie(request, cookie_name)
        request.session.delete()
        request.session = None
        return u, True # we return a invalidated user object, so that
                       # following auth methods can get the name of
                       # the user who logged out
    # refresh cookie lifetime
    setSessionCookie(request, u, securitystringcache=ussc, secidx=secidx)
    return u, True # use True to get other methods called, too

def moin_anon_session(request, **kw):
    """Anonymous session support.

    If you need sessions for anonymous users add this to the config.auth list
    and set config.anonymous_cookie_lifetime (in hours, can be fractional.)
    """
    user_obj = kw.get('user_obj')

    if request.session or not hasattr(request.cfg, 'anonymous_cookie_lifetime'):
        return user_obj, True

    # moin_session can handle this cookie and migrate
    # the session to a known one when you log in
    session_name = generate_security_string(32)
    setAnonCookie(request, session_name)
    return user_obj, True
