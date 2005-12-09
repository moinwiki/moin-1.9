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
       (we maybe add some more here)

    Use code like this to get them:
        name = kw.get('name') or ''
        password = kw.get('password') or ''
        login = kw.get('login')
        logout = kw.get('logout')
        request.log("got name=%s len(password)=%d login=%r logout=%r" % (name, len(password), login, logout))
    
    The called auth method then must return a tuple (user_obj, continue_flag).
    user_obj is either a User object or None if it could not make one.
    continue_flag is a boolean indication whether the auth loop shall continue
    trying other auth methods (or not).

    There are the possible cases for the returned tuple:
    user, False == we managed to authentify a user and we don't need to continue
    user, True  == makes no sense (unused)
    None, False == we could not authenticate the user and this is final, we
                   don't want to try other auth methods to authenticate him
    None, True  == we could not authentifacte the user, but we want to continue
                   trying with other auth methods

    The methods give a kw arg "auth_attribs" to User.__init__ that tells
    which user attribute names are DETERMINED and set by this auth method and
    must not get changed by the user using the UserPreferences form.
    It also gives a kw arg "auth_method" that tells the name of the auth
    method that authentified the user.
    
    @copyright: (c) Bastian Blank, Florian Festi, Thomas Waldmann
    @copyright: MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import Cookie
from MoinMoin import user

def moin_cookie(request, **kw):
    """ authenticate via the MOIN_ID cookie """
    if kw.get('login'):
        name = kw.get('name')
        password = kw.get('password')
        u = user.User(request, name=name, password=password,
                      auth_method='login_userpassword')
        if u.valid:
            request.user = u # needed by setCookie
            request.setCookie()
            return u, False
        return None, True

    if kw.get('logout'):
        # clear the cookie in the browser and locally. Does not
        # check if we have a valid user logged, just make sure we
        # don't have one after this call.
        request.deleteCookie()
        return None, True
    
    try:
        cookie = Cookie.SimpleCookie(request.saved_cookie)
    except Cookie.CookieError:
        # ignore invalid cookies, else user can't relogin
        cookie = None
    if cookie and cookie.has_key('MOIN_ID'):
        u = user.User(request, id=cookie['MOIN_ID'].value,
                      auth_method='moin_cookie', auth_attribs=())
        if u.valid:
            return u, False
    return None, True


#
#   idea: maybe we should call back to the request object like:
#         username, password, authenticated, authtype = request.getUserPassAuth()
#	 WhoEver   geheim    false          basic      (twisted, doityourself pw check)
#	 WhoEver   None      true           basic/...  (apache)
#	 
#        thus, the server specific code would stay in request object implementation.
#
#     THIS IS NOT A WIKI PAGE ;-)
	 
def http(request, **kw):
    """ authenticate via http basic/digest/ntlm auth """
    from MoinMoin.request import RequestTwisted
    u = None
    # check if we are running Twisted
    if isinstance(request, RequestTwisted):
        username = request.twistd.getUser()
        password = request.twistd.getPassword()
        # when using Twisted http auth, we use username and password from
        # the moin user profile, so both can be changed by user.
        u = user.User(request, auth_username=username, password=password,
                      auth_method='http', auth_attribs=())

    else:
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
        return u, False
    else:
        return None, True

def sslclientcert(request, **kw):
    """ authenticate via SSL client certificate """
    from MoinMoin.request import RequestTwisted
    u = None
    changed = False
    # check if we are running Twisted
    if isinstance(request, RequestTwisted):
        return u # not supported if we run twisted
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
                for uid in user.getUserList():
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

    if u:
        u.create_or_update(changed)
    if u and u.valid:
        return u, False
    else:
        return None, True

def interwiki(request, **kw):
    # TODO use auth_method and auth_attribs for User object
    # TODO use tuples as return value
    if request.form.has_key("user"):
        username = request.form["user"][0]
    else:
        return None
    passwd = None
    if request.form.has_key("passwd"):
        passwd = request.form["passwd"][0]

    wikitag, wikiurl, wikitail, err = wikiutil.resolve_wiki(username)

    if err or wikitag not in request.cfg.trusted_wikis:
        return None
    
    if passwd:
        import xmlrpclib
        homewiki = xmlrpclib.Server(wikiurl + "?action=xmlrpc2")
        account_data = homewiki.getUser(wikitail, passwd)
        if isinstance(account_data, str):
            # show error message
            return None
        
        u = user.User(request, name=username)
        for key, value in account_data.iteritems():
            if key not in ["may", "id", "valid", "trusted"
                           "auth_username",
                           "name", "aliasname",
                           "enc_passwd"]:
                setattr(u, key, value)
        u.save()
        request.user = u
        request.setCookie()
        return u
    else:
        pass
        # XXX redirect to homewiki


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
        """ @param apps A list of the enabled applications. See above for
            possible keys.
            @param s_path The path where the PHP sessions are stored.
            @param s_prefix The prefix of the session files.
        """
        
        self.s_path = s_path
        self.s_prefix = s_prefix
        self.apps = apps

    def __call__(self, request):
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
        
        import Cookie
        import urllib
        from MoinMoin.user import User
    
        from MoinMoin.util import sessionParser
    
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
                return None, True
            
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
                return user, False # return user object and stop processing auth method list
        return None, True # return None and continue with next method in auth list

