# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - modular authentication code

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
       (we maybe add some more here)

    Use code like this to get them:
        name = kw.get('name') or ''
        password = kw.get('password') or ''
        login = kw.get('login')
        logout = kw.get('logout')
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

    TODO: check against other cookie work (see wiki)  
          reduce amount of XXX
          
    @copyright: 2005-2006 Bastian Blank, Florian Festi, MoinMoin:ThomasWaldmann,
                          MoinMoin:AlexanderSchremmer, Nick Phillips,
                          MoinMoin:FrankieChow, MoinMoin:NirSoffer
    @license: GNU GPL, see COPYING for details.
"""

import time, Cookie
from MoinMoin import user

# cookie names
MOIN_SESSION = 'MOIN_SESSION'

import hmac, random

def generate_security_string(length):
    """ generate a random length (length/2 .. length) string with random content """
    random_length = random.randint(length/2, length)
    safe = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-'
    return ''.join([random.choice(safe) for i in range(random_length)])

def make_security_hash(request, data, securitystring=''):
    """ generate a hash string based on site configuration's cfg.cookie_secret,
        securitystring and the data.
    """
    return hmac.new(request.cfg.cookie_secret + securitystring, data).hexdigest()

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

def setCookie(request, u, cookie_name, cookie_string):
    """ Set cookie for the user obj u
    
    cfg.cookie_lifetime and the user 'remember_me' setting set the
    lifetime of the cookie. lifetime in int hours, see table:
    
    value   cookie lifetime
    ----------------------------------------------------------------
     = 0    forever, ignoring user 'remember_me' setting
     > 0    n hours, or forever if user checked 'remember_me'
     < 0    -n hours, ignoring user 'remember_me' setting
    """
    # Calculate cookie maxage and expires
    lifetime = int(request.cfg.cookie_lifetime) * 3600 
    forever = 10 * 365 * 24 * 3600 # 10 years
    now = time.time()
    if not lifetime:
        maxage = forever
    elif lifetime > 0:
        if u.remember_me:
            maxage = forever
        else:
            maxage = lifetime
    elif lifetime < 0:
        maxage = (-lifetime)
    expires = now + maxage
    
    cookie = makeCookie(request, cookie_name, cookie_string, maxage, expires)
    # Set cookie
    request.setHttpHeader(cookie)
    # IMPORTANT: Prevent caching of current page and cookie
    request.disableHttpCaching()

def setSessionCookie(request, u):
    """ Set moin_session cookie for user obj u """
    import base64
    cfg = request.cfg
    enc_username = base64.encodestring(u.auth_username)
    enc_id = base64.encodestring(u.id)
    # XXX - should include expiry!
    cookie_body = "username=%s:id=%s" % (enc_username, enc_id)
    cookie_hash = make_security_hash(request, cookie_body)
    cookie_string = ':'.join([cookie_hash, cookie_body])
    setCookie(request, u, MOIN_SESSION, cookie_string)

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
    
    if verbose: request.log("auth.moin_session: name=%s login=%r logout=%r user_obj=%r" % (username, login, logout, user_obj))

    if login:
        if verbose: request.log("moin_session performing login action")

        # Has any other method successfully authenticated?
        if user_obj is not None and user_obj.valid:
            # Yes - set up session cookie
            if verbose: request.log("moin_session got valid user from previous auth method, setting cookie...")
            if verbose: request.log("moin_session got auth_username %s." % user_obj.auth_username)
            setSessionCookie(request, user_obj)
            return user_obj, True # we make continuing possible, e.g. for smbmount
        else:
            # No other method succeeded, so allow continuation...
            # XXX Cookie clear here???
            if verbose: request.log("moin_session did not get valid user from previous auth method, doing nothing")
            return user_obj, True

    try:
        if verbose: request.log("trying to get cookie...")
        cookie = Cookie.SimpleCookie(request.saved_cookie)
    except Cookie.CookieError:
        # ignore invalid cookies, else user can't relogin
        if verbose: request.log("caught Cookie.CookieError")
        cookie = None

    if not (cookie is not None and cookie.has_key(cookie_name)):
        # No valid cookie
        if verbose: request.log("either no cookie or no %s key" % cookie_name)
        return user_obj, True
    
    try:
        cookie_hash, cookie_body = cookie[cookie_name].value.split(':', 1)
    except ValueError:
        # Invalid cookie
        if verbose: request.log("invalid cookie format: (%s)" % cookie[cookie_name].value)
        return user_obj, True
    
    if cookie_hash != make_security_hash(request, cookie_body):
        # Invalid cookie
        # XXX Cookie clear here???
        if verbose: request.log("cookie recovered had invalid hash")
        return user_obj, True

    # We can trust the cookie
    if verbose: request.log("Cookie OK, authenticated.")
    params = { 'username': '', 'id': '' }
    cookie_pairs = cookie_body.split(":")
    for key, value in [pair.split("=", 1) for pair in cookie_pairs]:
        params[key] = base64.decodestring(value) # assuming all values are base64 encoded
    # XXX Should check expiry from cookie
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
        deleteCookie(request, cookie_name)
        return u, True # we return a invalidated user object, so that
                       # following auth methods can get the name of
                       # the user who logged out
    setSessionCookie(request, u) # refreshes cookie lifetime
    return u, True # use True to get other methods called, too

