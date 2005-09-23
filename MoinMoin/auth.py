# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - modular authentication code

    @copyright: (c) Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import Cookie
from MoinMoin.user import User

def moin_cookie(request):
    """ authenticate via the MOIN_ID cookie """
    try:
        cookie = Cookie.SimpleCookie(request.saved_cookie)
    except Cookie.CookieError:
        # ignore invalid cookies, else user can't relogin
        cookie = None
    if cookie and cookie.has_key('MOIN_ID'):
        user = User(request, id=cookie['MOIN_ID'].value)
        if user.valid:
            return user

    return None


"""
   idea: maybe we should call back to the request object like:
         username, password, authenticated, authtype = request.getUserPassAuth()
	 WhoEver   geheim    false          basic      (twisted, doityourself pw check)
	 WhoEver   None      true           basic/...  (apache)
	 
         thus, the server specific code would stay in request object implementation.
"""
	 
def http(request):
    """ authenticate via http basic/digest/ntlm auth """
    from MoinMoin.request import RequestTwisted
    user = None
    # check if we are running Twisted
    if isinstance(request, RequestTwisted):
        username = request.twistd.getUser()
        password = request.twistd.getPassword()
        user = User(request, auth_username=username, password=password)

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
            user = User(request, auth_username=username)

    # XXX create (user? maybe should not happen here, but one layer higher to be
    # common for all auth methods

    if user and user.valid:
        return user
    else:
        return None

def interwiki(request):
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
        
        user = User(request, name=username)
        for key, value in account_data.iteritems():
            if key not in ["may", "id", "valid", "trusted"
                           "auth_username",
                           "name", "aliasname",
                           "enc_passwd"]:
                setattr(user, key, value)
        user.save()
        request.user = user
        request.setCookie()
        return user
    else:
        pass
        # XXX redirect to homewiki

