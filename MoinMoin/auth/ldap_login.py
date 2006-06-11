# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - LDAP / Active Directory authentication

    This code only creates a user object, the session has to be established by
    the auth.moin_session auth plugin.
    
    @copyright: 2006 by MoinMoin:ThomasWaldmann, Nick Phillips
    @license: GNU GPL, see COPYING for details.
"""
import sys, re
import traceback
import ldap
from MoinMoin import user

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
            
            u = user.User(request, auth_username=username, password="{SHA}NotStored", auth_method='ldap', auth_attribs=('name', 'password', 'email', 'mailto_author',))
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
    return u, True # moin_session has to set the cookie

