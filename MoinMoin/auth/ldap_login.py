# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - LDAP / Active Directory authentication

    This code only creates a user object, the session has to be established by
    the auth.moin_session auth plugin.

    python-ldap needs to be at least 2.0.0pre06 (available since mid 2002) for
    ldaps support - some older debian installations (woody and older?) require
    libldap2-tls and python2.x-ldap-tls, otherwise you get ldap.SERVER_DOWN:
    "Can't contact LDAP server" - more recent debian installations have tls
    support in libldap2 (see dependency on gnutls) and also in python-ldap.

    TODO: migrate configuration items to constructor parameters,
          allow more configuration (alias name, ...) by using
          callables as parameters

    @copyright: 2006-2008 MoinMoin:ThomasWaldmann,
                2006 Nick Phillips
    @license: GNU GPL, see COPYING for details.
"""
import ldap

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import user
from MoinMoin.auth import BaseAuth, CancelLogin, ContinueLogin


class LDAPAuth(BaseAuth):
    """ get authentication data from form, authenticate against LDAP (or Active
        Directory), fetch some user infos from LDAP and create a user object
        for that user. The session is kept by the moin_session auth plugin.
    """

    login_inputs = ['username', 'password']
    logout_possible = True
    name = 'ldap'

    def login(self, request, user_obj, **kw):
        username = kw.get('username')
        password = kw.get('password')
        _ = request.getText

        cfg = request.cfg
        verbose = cfg.ldap_verbose

        # we require non-empty password as ldap bind does a anon (not password
        # protected) bind if the password is empty and SUCCEEDS!
        if not password:
            return ContinueLogin(user_obj, _('Missing password. Please enter user name and password.'))

        try:
            try:
                u = None
                dn = None
                coding = cfg.ldap_coding
                if verbose: logging.info("Setting misc. ldap options...")
                ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3) # ldap v2 is outdated
                ldap.set_option(ldap.OPT_REFERRALS, cfg.ldap_referrals)
                ldap.set_option(ldap.OPT_NETWORK_TIMEOUT, cfg.ldap_timeout)

                starttls = cfg.ldap_start_tls
                if hasattr(ldap, 'TLS_AVAIL') and ldap.TLS_AVAIL:
                    for option, value in (
                        (ldap.OPT_X_TLS_CACERTDIR, cfg.ldap_tls_cacertdir),
                        (ldap.OPT_X_TLS_CACERTFILE, cfg.ldap_tls_cacertfile),
                        (ldap.OPT_X_TLS_CERTFILE, cfg.ldap_tls_certfile),
                        (ldap.OPT_X_TLS_KEYFILE, cfg.ldap_tls_keyfile),
                        (ldap.OPT_X_TLS_REQUIRE_CERT, cfg.ldap_tls_require_cert),
                        (ldap.OPT_X_TLS, starttls),
                        #(ldap.OPT_X_TLS_ALLOW, 1),
                    ):
                        if value:
                            ldap.set_option(option, value)

                server = cfg.ldap_uri
                if verbose: logging.info("Trying to initialize %r." % server)
                l = ldap.initialize(server)
                if verbose: logging.info("Connected to LDAP server %r." % server)

                if starttls and server.startswith('ldap:'):
                    if verbose: logging.info("Trying to start TLS to %r." % server)
                    try:
                        l.start_tls_s()
                        if verbose: logging.info("Using TLS to %r." % server)
                    except (ldap.SERVER_DOWN, ldap.CONNECT_ERROR), err:
                        if verbose: logging.info("Couldn't establish TLS to %r (err: %s)." % (server, str(err)))
                        raise

                # you can use %(username)s and %(password)s here to get the stuff entered in the form:
                ldap_binddn = cfg.ldap_binddn % locals()
                ldap_bindpw = cfg.ldap_bindpw % locals()
                l.simple_bind_s(ldap_binddn.encode(coding), ldap_bindpw.encode(coding))
                if verbose: logging.info("Bound with binddn %r" % ldap_binddn)

                # you can use %(username)s here to get the stuff entered in the form:
                filterstr = cfg.ldap_filter % locals()
                if verbose: logging.info("Searching %r" % filterstr)
                attrs = [getattr(cfg, attr) for attr in [
                                         'ldap_email_attribute',
                                         'ldap_aliasname_attribute',
                                         'ldap_surname_attribute',
                                         'ldap_givenname_attribute',
                                         ] if getattr(cfg, attr) is not None]
                lusers = l.search_st(cfg.ldap_base, cfg.ldap_scope, filterstr.encode(coding),
                                     attrlist=attrs, timeout=cfg.ldap_timeout)
                # we remove entries with dn == None to get the real result list:
                lusers = [(dn, ldap_dict) for dn, ldap_dict in lusers if dn is not None]
                if verbose:
                    for dn, ldap_dict in lusers:
                        logging.info("dn:%r" % dn)
                        for key, val in ldap_dict.items():
                            logging.info("    %r: %r" % (key, val))

                result_length = len(lusers)
                if result_length != 1:
                    if result_length > 1:
                        logging.info("Search found more than one (%d) matches for %r." % (result_length, filterstr))
                    if result_length == 0:
                        if verbose: logging.info("Search found no matches for %r." % (filterstr, ))
                    return CancelLogin(_("Invalid username or password."))

                dn, ldap_dict = lusers[0]
                if not cfg.ldap_bindonce:
                    if verbose: logging.info("DN found is %r, trying to bind with pw" % dn)
                    l.simple_bind_s(dn, password.encode(coding))
                    if verbose: logging.info("Bound with dn %r (username: %r)" % (dn, username))

                if cfg.ldap_email_callback is None:
                    if cfg.ldap_email_attribute:
                        email = ldap_dict.get(cfg.ldap_email_attribute, [''])[0].decode(coding)
                    else:
                        email = None
                else:
                    email = cfg.ldap_email_callback(ldap_dict)

                aliasname = ''
                try:
                    aliasname = ldap_dict[cfg.ldap_aliasname_attribute][0]
                except (KeyError, IndexError):
                    pass
                if not aliasname:
                    sn = ldap_dict.get(cfg.ldap_surname_attribute, [''])[0]
                    gn = ldap_dict.get(cfg.ldap_givenname_attribute, [''])[0]
                    if sn and gn:
                        aliasname = "%s, %s" % (sn, gn)
                    elif sn:
                        aliasname = sn
                aliasname = aliasname.decode(coding)

                if email:
                    u = user.User(request, auth_username=username, password="{SHA}NotStored", auth_method=self.name, auth_attribs=('name', 'password', 'email', 'mailto_author', ))
                    u.email = email
                else:
                    u = user.User(request, auth_username=username, password="{SHA}NotStored", auth_method=self.name, auth_attribs=('name', 'password', 'mailto_author', ))
                u.name = username
                u.aliasname = aliasname
                u.remember_me = 0 # 0 enforces cookie_lifetime config param
                if verbose: logging.info("creating userprefs with name %r email %r alias %r" % (username, email, aliasname))

            except ldap.INVALID_CREDENTIALS, err:
                logging.info("invalid credentials (wrong password?) for dn %r (username: %r)" % (dn, username))
                return CancelLogin(_("Invalid username or password."))

            if u:
                u.create_or_update(True)
            return ContinueLogin(u)

        except:
            logging.exception("caught an exception, traceback follows...")
            return CancelLogin(None)

