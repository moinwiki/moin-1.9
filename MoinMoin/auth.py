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
    
    @copyright: 2005-2006 Bastian Blank, Florian Festi, Thomas Waldmann
    @copyright: 2005-2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import time, Cookie
from MoinMoin import user

def log(request, **kw):
    """ just log the call, do nothing else """
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')
    request.log("auth.log: name=%s login=%r logout=%r user_obj=%r" % (username, login, logout, user_obj))
    return user_obj, True

# some cookie functions used by moin_cookie auth
def makeCookie(request, moin_id, maxage, expires):
    """ calculate a MOIN_ID cookie """
    c = Cookie.SimpleCookie()
    cfg = request.cfg
    c['MOIN_ID'] = moin_id
    c['MOIN_ID']['max-age'] = maxage
    if cfg.cookie_domain:
        c['MOIN_ID']['domain'] = cfg.cookie_domain
    if cfg.cookie_path:
        c['MOIN_ID']['path'] = cfg.cookie_path
    else:
        path = request.getScriptname()
        if not path:
            path = '/'
        c['MOIN_ID']['path'] = path
    # Set expires for older clients
    c['MOIN_ID']['expires'] = request.httpDate(when=expires, rfc='850')        
    return c.output()

def setCookie(request, u):
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
    forever = 10*365*24*3600 # 10 years
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
    
    cookie = makeCookie(request, u.id, maxage, expires)
    # Set cookie
    request.setHttpHeader(cookie)
    # IMPORTANT: Prevent caching of current page and cookie
    request.disableHttpCaching()

def deleteCookie(request):
    """ Delete the user cookie by sending expired cookie with null value

    According to http://www.cse.ohio-state.edu/cgi-bin/rfc/rfc2109.html#sec-4.2.2
    Deleted cookie should have Max-Age=0. We also have expires
    attribute, which is probably needed for older browsers.

    Finally, delete the saved cookie and create a new user based on the new settings.
    """
    moin_id = ''
    maxage = 0
    # Set expires to one year ago for older clients
    expires = time.time() - (3600 * 24 * 365) # 1 year ago
    cookie = makeCookie(request, moin_id, maxage, expires) 
    # Set cookie
    request.setHttpHeader(cookie)
    # IMPORTANT: Prevent caching of current page and cookie        
    request.disableHttpCaching()

def moin_cookie(request, **kw):
    """ authenticate via the MOIN_ID cookie """
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')
    #request.log("auth.moin_cookie: name=%s login=%r logout=%r user_obj=%r" % (username, login, logout, user_obj))
    if login:
        u = user.User(request, name=username, password=password,
                      auth_method='login_userpassword')
        if u.valid:
            setCookie(request, u)
            return u, True # we make continuing possible, e.g. for smbmount
        return user_obj, True

    try:
        cookie = Cookie.SimpleCookie(request.saved_cookie)
    except Cookie.CookieError:
        # ignore invalid cookies, else user can't relogin
        cookie = None
    if cookie and cookie.has_key('MOIN_ID'):
        u = user.User(request, id=cookie['MOIN_ID'].value,
                      auth_method='moin_cookie', auth_attribs=())

        if logout:
            u.valid = 0 # just make user invalid, but remember him

        if u.valid:
            setCookie(request, u) # refreshes cookie lifetime
            return u, True # use True to get other methods called, too
        else: # logout or invalid user
            deleteCookie(request)
            return u, True # we return a invalidated user object, so that
                           # following auth methods can get the name of
                           # the user who logged out
    return user_obj, True


def http(request, **kw):
    """ authenticate via http basic/digest/ntlm auth """
    from MoinMoin.request import RequestTwisted, RequestCLI
    user_obj = kw.get('user_obj')
    u = None
    # check if we are running Twisted
    if isinstance(request, RequestTwisted):
        username = request.twistd.getUser()
        password = request.twistd.getPassword()
        # when using Twisted http auth, we use username and password from
        # the moin user profile, so both can be changed by user.
        u = user.User(request, auth_username=username, password=password,
                      auth_method='http', auth_attribs=())

    elif not isinstance(request, RequestCLI):
        env = request.env
        auth_type = env.get('AUTH_TYPE','')
        if auth_type in ['Basic', 'Digest', 'NTLM', 'Negotiate',]:
            username = env.get('REMOTE_USER','')
            if auth_type in ('NTLM', 'Negotiate',):
                # converting to standard case so the user can even enter wrong case
                # (added since windows does not distinguish between e.g.
                #  "Mike" and "mike")
                username = username.split('\\')[-1] # split off domain e.g.
                                                    # from DOMAIN\user
                # this "normalizes" the login name from {meier, Meier, MEIER} to Meier
                # put a comment sign in front of next line if you don't want that:
                username = username.title()
            # when using http auth, we have external user name and password,
            # we don't use the moin user profile for those attributes.
            u = user.User(request, auth_username=username,
                          auth_method='http', auth_attribs=('name', 'password'))

    if u:
        u.create_or_update()
    if u and u.valid:
        return u, True # True to get other methods called, too
    else:
        return user_obj, True

def sslclientcert(request, **kw):
    """ authenticate via SSL client certificate """
    from MoinMoin.request import RequestTwisted
    user_obj = kw.get('user_obj')
    u = None
    changed = False
    # check if we are running Twisted
    if isinstance(request, RequestTwisted):
        return user_obj, True # not supported if we run twisted
        # Addendum: this seems to need quite some twisted insight and coding.
        # A pointer i got on #twisted: divmod's vertex.sslverify
        # If you really need this, feel free to implement and test it and
        # submit a patch if it works.
    else:
        env = request.env
        if env.get('SSL_CLIENT_VERIFY', 'FAILURE') == 'SUCCESS':
            # if we only want to accept some specific CA, do a check like:
            # if env.get('SSL_CLIENT_I_DN_OU') == "http://www.cacert.org"
            email = env.get('SSL_CLIENT_S_DN_Email', '')
            email_lower = email.lower()
            commonname = env.get('SSL_CLIENT_S_DN_CN', '')
            commonname_lower = commonname.lower()
            if email_lower or commonname_lower:
                for uid in user.getUserList(request):
                    u = user.User(request, uid,
                                  auth_method='sslclientcert', auth_attribs=())
                    if email_lower and u.email.lower() == email_lower:
                        u.auth_attribs = ('email', 'password')
                        #this is only useful if same name should be used, as
                        #commonname is likely no CamelCase WikiName
                        #if commonname_lower != u.name.lower():
                        #    u.name = commonname
                        #    changed = True
                        #u.auth_attribs = ('email', 'name', 'password')
                        break
                    if commonname_lower and u.name.lower() == commonname_lower:
                        u.auth_attribs = ('name', 'password')
                        #this is only useful if same email should be used as
                        #specified in certificate.
                        #if email_lower != u.email.lower():
                        #    u.email = email
                        #    changed = True
                        #u.auth_attribs = ('name', 'email', 'password')
                        break
                else:
                    u = None
                if u is None:
                    # user wasn't found, so let's create a new user object
                    u = user.User(request, name=commonname_lower, auth_username=commonname_lower)

    if u:
        u.create_or_update(changed)
    if u and u.valid:
        return u, True
    else:
        return user_obj, True


def smb_mount(request, **kw):
    """ (u)mount a SMB server's share for username (using username/password for
        authentication at the SMB server). This can be used if you need access
        to files on some share via the wiki, but needs more code to be useful.
        If you don't need it, don't use it.
    """
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')
    cfg = request.cfg
    verbose = cfg.smb_verbose
    if verbose: request.log("got name=%s login=%r logout=%r" % (username, login, logout))
    
    # we just intercept login to mount and logout to umount the smb share
    if login or logout:
        import os, pwd, subprocess
        web_username = cfg.smb_dir_user
        web_uid = pwd.getpwnam(web_username)[2] # XXX better just use current uid?
        if logout and user_obj: # logout -> we don't have username in form
            username = user_obj.name # so we take it from previous auth method (moin_cookie e.g.)
        mountpoint = cfg.smb_mountpoint % {
            'username': username,
        }
        if login:
            cmd = u"sudo mount -t cifs -o user=%(user)s,domain=%(domain)s,uid=%(uid)d,dir_mode=%(dir_mode)s,file_mode=%(file_mode)s,iocharset=%(iocharset)s //%(server)s/%(share)s %(mountpoint)s >>%(log)s 2>&1"
        elif logout:
            cmd = u"sudo umount %(mountpoint)s >>%(log)s 2>&1"
            
        cmd = cmd % {
            'user': username,
            'uid': web_uid,
            'domain': cfg.smb_domain,
            'server': cfg.smb_server,
            'share': cfg.smb_share,
            'mountpoint': mountpoint,
            'dir_mode': cfg.smb_dir_mode,
            'file_mode': cfg.smb_file_mode,
            'iocharset': cfg.smb_iocharset,
            'log': cfg.smb_log,
        }
        env = os.environ.copy()
        if login:
            try:
                os.makedirs(mountpoint) # the dir containing the mountpoint must be writeable for us!
            except OSError, err:
                pass
            env['PASSWD'] = password.encode(cfg.smb_coding)
        subprocess.call(cmd.encode(cfg.smb_coding), env=env, shell=True)
    return user_obj, True


def ldap_login(request, **kw):
    """ get authentication data from form, authenticate against LDAP (or Active Directory),
        fetch some user infos from LDAP and create a user profile for that user that must
        be used by subsequent auth plugins (like moin_cookie) as we never return a user
        object from ldap_login.
    """
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')

    cfg = request.cfg
    verbose = cfg.ldap_verbose
    
    if verbose: request.log("got name=%s login=%r logout=%r" % (username, login, logout))
    
    # we just intercept login and logout for ldap, other requests have to be
    # handled by another auth handler
    if not login and not logout:
        return user_obj, True
    
    import sys, re
    import ldap
    import traceback

    u = None
    coding = cfg.ldap_coding
    try:
        if verbose: request.log("LDAP: Trying to initialize %s." % cfg.ldap_uri)
        l = ldap.initialize(cfg.ldap_uri)
        if verbose: request.log("LDAP: Connected to LDAP server %s." % cfg.ldap_uri)
        # you can use %(username)s and %(password)s here to get the stuff entered in the form:
        ldap_binddn = cfg.ldap_binddn % locals()
        ldap_bindpw = cfg.ldap_bindpw % locals()
        l.simple_bind_s(ldap_binddn.encode(coding), ldap_bindpw.encode(coding))
        if verbose: request.log("LDAP: Bound with binddn %s" % ldap_binddn)

        filterstr = "(%s=%s)" % (cfg.ldap_name_attribute, username)
        if verbose: request.log("LDAP: Searching %s" % filterstr)
        lusers = l.search_st(cfg.ldap_base, cfg.ldap_scope,
                             filterstr.encode(coding), timeout=cfg.ldap_timeout)
        result_length = len(lusers)
        if result_length != 1:
            if result_length > 1:
                request.log("LDAP: Search found more than one (%d) matches for %s." % (len(lusers), filterstr))
            if result_length == 0:
                if verbose: request.log("LDAP: Search found no matches for %s." % (filterstr, ))
            return user_obj, True

        dn, ldap_dict = lusers[0]
        if verbose:
            request.log("LDAP: debug lusers = %r" % lusers)
            for key,val in ldap_dict.items():
                request.log("LDAP: %s: %s" % (key, val))

        try:
            if verbose: request.log("LDAP: DN found is %s, trying to bind with pw" % dn)
            l.simple_bind_s(dn, password.encode(coding))
            if verbose: request.log("LDAP: Bound with dn %s (username: %s)" % (dn, username))
            
            email = ldap_dict.get(cfg.ldap_email_attribute, [''])[0]
            email = email.decode(coding)
            sn, gn = ldap_dict.get('sn', [''])[0], ldap_dict.get('givenName', [''])[0]
            aliasname = ''
            if sn and gn:
                aliasname = "%s, %s" % (sn, gn)
            elif sn:
                aliasname = sn
            aliasname = aliasname.decode(coding)
            
            u = user.User(request, auth_username=username, password=password, auth_method='ldap', auth_attribs=('name', 'password', 'email', 'mailto_author',))
            u.name = username
            u.aliasname = aliasname
            u.email = email
            u.remember_me = 0 # 0 enforces cookie_lifetime config param
            if verbose: request.log("LDAP: creating userprefs with name %s email %s alias %s" % (username, email, aliasname))
            
        except ldap.INVALID_CREDENTIALS, err:
            request.log("LDAP: invalid credentials (wrong password?) for dn %s (username: %s)" % (dn, username))

    except:
        info = sys.exc_info()
        request.log("LDAP: caught an exception, traceback follows...")
        request.log(''.join(traceback.format_exception(*info)))

    if u:
        u.create_or_update(True)
    return user_obj, True # moin_cookie has to set the cookie and return the user obj


def interwiki(request, **kw):
    # TODO use auth_method and auth_attribs for User object
    username = kw.get('name')
    password = kw.get('password')
    login = kw.get('login')
    logout = kw.get('logout')
    user_obj = kw.get('user_obj')

    if login:
        wikitag, wikiurl, wikitail, err = wikiutil.resolve_wiki(username)

        if err or wikitag not in request.cfg.trusted_wikis:
            return user_obj, True
        
        if password:
            import xmlrpclib
            homewiki = xmlrpclib.Server(wikiurl + "?action=xmlrpc2")
            account_data = homewiki.getUser(wikitail, password)
            if isinstance(account_data, str):
                # show error message
                return user_obj, True
            
            u = user.User(request, name=username)
            for key, value in account_data.iteritems():
                if key not in ["may", "id", "valid", "trusted"
                               "auth_username",
                               "name", "aliasname",
                               "enc_passwd"]:
                    setattr(u, key, value)
            u.save()
            setCookie(request, u)
            return u, True
        else:
            pass
            # XXX redirect to homewiki
    
    return user_obj, True


class php_session:
    """ Authentication module for PHP based frameworks
        Authenticates via PHP session cookie. Currently supported systems:

        * eGroupware 1.2 ("egw")
         * You need to configure eGroupware in the "header setup" to use
           "php sessions plus restore"

        @copyright: 2005 by MoinMoin:AlexanderSchremmer
            - Thanks to Spreadshirt
    """

    def __init__(self, apps=['egw'], s_path="/tmp", s_prefix="sess_"):
        """ @param apps: A list of the enabled applications. See above for
            possible keys.
            @param s_path: The path where the PHP sessions are stored.
            @param s_prefix: The prefix of the session files.
        """
        
        self.s_path = s_path
        self.s_prefix = s_prefix
        self.apps = apps

    def __call__(self, request, **kw):
        def handle_egroupware(session):
            """ Extracts name, fullname and email from the session. """
            username = session['egw_session']['session_lid'].split("@", 1)[0]
            known_accounts = session['egw_info_cache']['accounts']['cache']['account_data']
            
            # if the next line breaks, then the cache was not filled with the current
            # user information
            user_info = [value for key, value in known_accounts.items()
                         if value['account_lid'] == username][0]
            name = user_info.get('fullname', '')
            email = user_info.get('email', '')
            
            dec = lambda x: x and x.decode("iso-8859-1")
            
            return dec(username), dec(email), dec(name)
        
        import Cookie, urllib
        from MoinMoin.user import User
        from MoinMoin.util import sessionParser
    
        user_obj = kw.get('user_obj')
        try:
            cookie = Cookie.SimpleCookie(request.saved_cookie)
        except Cookie.CookieError: # ignore invalid cookies
            cookie = None
        if cookie:
            for cookiename in cookie.keys():
                cookievalue = urllib.unquote(cookie[cookiename].value).decode('iso-8859-1')
                session = sessionParser.loadSession(cookievalue, path=self.s_path, prefix=self.s_prefix)
                if session:
                    if "egw" in self.apps and session.get('egw_session', None):
                        username, email, name = handle_egroupware(session)
                        break
            else:
                return user_obj, True
            
            user = User(request, name=username, auth_username=username)
            
            changed = False
            if name != user.aliasname:
                user.aliasname = name
                changed = True
            if email != user.email:
                user.email = email
                changed = True
            
            if user:
                user.create_or_update(changed)
            if user and user.valid:
                return user, True # True to get other methods called, too
        return user_obj, True # continue with next method in auth list

