# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - LDAP / Active Directory authentication

    This code only creates a user object, the session has to be established by
    the auth.moin_session auth plugin.

    TODO: migrate configuration items to constructor parameters,
          allow more configuration (alias name, ...) by using
          callables as parameters

    @copyright: 2006 MoinMoin:ThomasWaldmann, Nick Phillips
    @license: GNU GPL, see COPYING for details.
"""
import sys
import ldap

from MoinMoin import user
from MoinMoin.auth import BaseAuth

class LDAPAuth(BaseAuth):
    """ get authentication data from form, authenticate against LDAP (or Active Directory),
        fetch some user infos from LDAP and create a user profile for that user that must
        be used by subsequent auth plugins (like moin_cookie) as we never return a user
        object from ldap_login.
    """

    login_inputs = ['username', 'password']
    logout_possible = True
    name = 'ldap'

    def login(self, request, user_obj, **kw):
        username = kw.get('username')
        password = kw.get('password')

        cfg = request.cfg
        verbose = cfg.ldap_verbose

        # we require non-empty password as ldap bind does a anon (not password
        # protected) bind if the password is empty and SUCCEEDS!
        if not password:
            return user_obj, True, None, None

        try:
            try:
                u = None
                dn = None
                coding = cfg.ldap_coding
                if verbose: request.log("LDAP: Setting misc. options...")
                # needed for Active Directory:
                ldap.set_option(ldap.OPT_REFERRALS, 0)

                server = cfg.ldap_uri
                if server.startswith('ldaps:'):
                    # TODO: refactor into LDAPAuth() constructor arguments!
                    # this is needed for self-signed ssl certs:
                    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                    # more stuff to try:
                    #ldap.set_option(ldap.OPT_X_TLS_ALLOW, 1)
                    #ldap.set_option(ldap.OPT_X_TLS_CERTFILE, LDAP_CACERTFILE)
                    #ldap.set_option(ldap.OPT_X_TLS_CACERTFILE,'/etc/httpd/ssl.crt/myCA-cacerts.pem')

                if verbose: request.log("LDAP: Trying to initialize %s." % server)
                l = ldap.initialize(server)
                if verbose: request.log("LDAP: Connected to LDAP server %s." % server)

                # you can use %(username)s and %(password)s here to get the stuff entered in the form:
                ldap_binddn = cfg.ldap_binddn % locals()
                ldap_bindpw = cfg.ldap_bindpw % locals()
                l.simple_bind_s(ldap_binddn.encode(coding), ldap_bindpw.encode(coding))
                if verbose: request.log("LDAP: Bound with binddn %s" % ldap_binddn)

                # you can use %(username)s here to get the stuff entered in the form:
                filterstr = cfg.ldap_filter % locals()
                if verbose: request.log("LDAP: Searching %s" % filterstr)
                lusers = l.search_st(cfg.ldap_base, cfg.ldap_scope, filterstr.encode(coding),
                                     attrlist=[cfg.ldap_email_attribute,
                                               cfg.ldap_aliasname_attribute,
                                               cfg.ldap_surname_attribute,
                                               cfg.ldap_givenname_attribute,
                                     ], timeout=cfg.ldap_timeout)
                # we remove entries with dn == None to get the real result list:
                lusers = [(dn, ldap_dict) for dn, ldap_dict in lusers if dn is not None]
                if verbose:
                    for dn, ldap_dict in lusers:
                        request.log("LDAP: dn:%s" % dn)
                        for key, val in ldap_dict.items():
                            request.log("    %s: %s" % (key, val))

                result_length = len(lusers)
                if result_length != 1:
                    if result_length > 1:
                        request.log("LDAP: Search found more than one (%d) matches for %s." % (result_length, filterstr))
                    if result_length == 0:
                        if verbose: request.log("LDAP: Search found no matches for %s." % (filterstr, ))
                    return None, False, None # if ldap returns unusable results, we veto the user and don't let him in

                dn, ldap_dict = lusers[0]
                if verbose: request.log("LDAP: DN found is %s, trying to bind with pw" % dn)
                l.simple_bind_s(dn, password.encode(coding))
                if verbose: request.log("LDAP: Bound with dn %s (username: %s)" % (dn, username))

                email = ldap_dict.get(cfg.ldap_email_attribute, [''])[0]
                email = email.decode(coding)

                aliasname = ''
                try:
                    aliasname = ldap_dict[cfg.ldap_aliasname_attribute][0]
                except (KeyError, IndexError):
                    sn = ldap_dict.get(cfg.ldap_surname_attribute, [''])[0]
                    gn = ldap_dict.get(cfg.ldap_givenname_attribute, [''])[0]
                    if sn and gn:
                        aliasname = "%s, %s" % (sn, gn)
                    elif sn:
                        aliasname = sn
                aliasname = aliasname.decode(coding)

                u = user.User(request, auth_username=username, password="{SHA}NotStored", auth_method=self.name, auth_attribs=('name', 'password', 'email', 'mailto_author',))
                u.name = username
                u.aliasname = aliasname
                u.email = email
                u.remember_me = 0 # 0 enforces cookie_lifetime config param
                if verbose: request.log("LDAP: creating userprefs with name %s email %s alias %s" % (username, email, aliasname))

            except ldap.INVALID_CREDENTIALS, err:
                request.log("LDAP: invalid credentials (wrong password?) for dn %s (username: %s)" % (dn, username))
                return None, False, None, None # if ldap says no, we veto the user and don't let him in

            if u:
                u.create_or_update(True)
            return u, True, None, None

        except:
            import traceback
            info = sys.exc_info()
            request.log("LDAP: caught an exception, traceback follows...")
            request.log(''.join(traceback.format_exception(*info)))
            return None, False, None, None # something went completely wrong, in doubt we veto the login

