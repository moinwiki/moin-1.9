# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.auth.ldap Tests

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import py.test
py.test.skip("Broken due to test Config refactoring")

from MoinMoin._tests.ldap_testbase import LDAPTstBase, LdapEnvironment, check_environ, SLAPD_EXECUTABLE
from MoinMoin._tests.ldap_testdata import *
from MoinMoin._tests import nuke_user, wikiconfig
from MoinMoin.auth import handle_login

# first check if we have python 2.4, python-ldap and slapd:
msg = check_environ()
if msg:
    py.test.skip(msg)
del msg

import ldap

class TestLDAPServer(LDAPTstBase):
    basedn = BASEDN
    rootdn = ROOTDN
    rootpw = ROOTPW
    slapd_config = SLAPD_CONFIG
    ldif_content = LDIF_CONTENT

    def testLDAP(self):
        """ Just try accessing the LDAP server and see if usera and userb are in LDAP. """
        server_uri = self.ldap_env.slapd.url
        base_dn = self.ldap_env.basedn
        lo = ldap.initialize(server_uri)
        ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3) # ldap v2 is outdated
        lo.simple_bind_s('', '')
        lusers = lo.search_st(base_dn, ldap.SCOPE_SUBTREE, '(uid=*)')
        uids = [ldap_dict['uid'][0] for dn, ldap_dict in lusers]
        assert 'usera' in uids
        assert 'userb' in uids

class TestMoinLDAPLogin(LDAPTstBase):
    basedn = BASEDN
    rootdn = ROOTDN
    rootpw = ROOTPW
    slapd_config = SLAPD_CONFIG
    ldif_content = LDIF_CONTENT

    class Config(wikiconfig.Config):
        from MoinMoin.auth.ldap_login import LDAPAuth
        server_uri = self.ldap_env.slapd.url # XXX no self
        base_dn = self.ldap_env.basedn
        ldap_auth1 = LDAPAuth(server_uri=server_uri, base_dn=base_dn, autocreate=True)
        auth = [ldap_auth1, ]

    def testMoinLDAPLogin(self):
        """ Just try accessing the LDAP server and see if usera and userb are in LDAP. """

        handle_auth = self.request.handle_auth

        # tests that must not authenticate:
        u = handle_login(self.request, None, username='', password='')
        assert u is None
        u = handle_login(self.request, None, username='usera', password='')
        assert u is None
        u = handle_login(self.request, None, username='usera', password='userawrong')
        assert u is None
        u = handle_login(self.request, None, username='userawrong', password='usera')
        assert u is None

        # tests that must authenticate:
        u1 = handle_login(self.request, None, username='usera', password='usera')
        assert u1 is not None
        assert u1.valid

        u2 = handle_login(self.request, None, username='userb', password='userb')
        assert u2 is not None
        assert u2.valid

        # check if usera and userb have different ids:
        assert u1.id != u2.id


class TestBugDefaultPasswd(LDAPTstBase):
    basedn = BASEDN
    rootdn = ROOTDN
    rootpw = ROOTPW
    slapd_config = SLAPD_CONFIG
    ldif_content = LDIF_CONTENT

    class Config(wikiconfig.Config):
        from MoinMoin.auth.ldap_login import LDAPAuth
        from MoinMoin.auth import MoinAuth
        server_uri = self.ldap_env.slapd.url # XXX no self
        base_dn = self.ldap_env.basedn
        ldap_auth = LDAPAuth(server_uri=server_uri, base_dn=base_dn, autocreate=True)
        moin_auth = MoinAuth()
        auth = [ldap_auth, moin_auth]

    def teardown_class(self):
        """ Stop slapd, remove LDAP server environment """
        #self.ldap_env.stop_slapd()  # it is already stopped
        self.ldap_env.destroy_env()

    def testBugDefaultPasswd(self):
        """ Login via LDAP (this creates user profile and up to 1.7.0rc1 it put
            a default password there), then try logging in via moin login using
            that default password or an empty password.
        """

        nuke_user(self.request, u'usera')

        # do a LDAPAuth login (as a side effect, this autocreates the user profile):
        u1 = handle_login(self.request, None, username='usera', password='usera')
        assert u1 is not None
        assert u1.valid

        # now we kill the LDAP server:
        #self.ldap_env.slapd.stop()

        # now try a MoinAuth login:
        # try the default password that worked in 1.7 up to rc1:
        u2 = handle_login(self.request, None, username='usera', password='{SHA}NotStored')
        assert u2 is None

        # try using no password:
        u2 = handle_login(self.request, None, username='usera', password='')
        assert u2 is None

        # try using wrong password:
        u2 = handle_login(self.request, None, username='usera', password='wrong')
        assert u2 is None


class TestTwoLdapServers:
    basedn = BASEDN
    rootdn = ROOTDN
    rootpw = ROOTPW
    slapd_config = SLAPD_CONFIG
    ldif_content = LDIF_CONTENT

    def setup_class(self):
        """ Create LDAP servers environment, start slapds """
        self.ldap_envs = []
        for instance in range(2):
            ldap_env = LdapEnvironment(self.basedn, self.rootdn, self.rootpw, instance=instance)
            ldap_env.create_env(slapd_config=self.slapd_config)
            started = ldap_env.start_slapd()
            if not started:
                py.test.skip("Failed to start %s process, please see your syslog / log files"
                             " (and check if stopping apparmor helps, in case you use it)." % SLAPD_EXECUTABLE)
            ldap_env.load_directory(ldif_content=self.ldif_content)
            self.ldap_envs.append(ldap_env)

    def teardown_class(self):
        """ Stop slapd, remove LDAP server environment """
        for ldap_env in self.ldap_envs:
            ldap_env.stop_slapd()
            ldap_env.destroy_env()

    def testLDAP(self):
        """ Just try accessing the LDAP servers and see if usera and userb are in LDAP. """
        for ldap_env in self.ldap_envs:
            server_uri = ldap_env.slapd.url
            base_dn = ldap_env.basedn
            lo = ldap.initialize(server_uri)
            ldap.set_option(ldap.OPT_PROTOCOL_VERSION, ldap.VERSION3) # ldap v2 is outdated
            lo.simple_bind_s('', '')
            lusers = lo.search_st(base_dn, ldap.SCOPE_SUBTREE, '(uid=*)')
            uids = [ldap_dict['uid'][0] for dn, ldap_dict in lusers]
            assert 'usera' in uids
            assert 'userb' in uids


class TestLdapFailover:
    basedn = BASEDN
    rootdn = ROOTDN
    rootpw = ROOTPW
    slapd_config = SLAPD_CONFIG
    ldif_content = LDIF_CONTENT

    class Config(wikiconfig.Config):
        from MoinMoin.auth.ldap_login import LDAPAuth
        authlist = []
        for ldap_env in self.ldap_envs: # XXX no self
            server_uri = ldap_env.slapd.url
            base_dn = ldap_env.basedn
            ldap_auth = LDAPAuth(server_uri=server_uri, base_dn=base_dn,
                                 autocreate=True,
                                 timeout=1) # short timeout, faster testing
            authlist.append(ldap_auth)
        auth = authlist

    def setup_class(self):
        """ Create LDAP servers environment, start slapds """
        self.ldap_envs = []
        for instance in range(2):
            ldap_env = LdapEnvironment(self.basedn, self.rootdn, self.rootpw, instance=instance)
            ldap_env.create_env(slapd_config=self.slapd_config)
            started = ldap_env.start_slapd()
            if not started:
                py.test.skip("Failed to start %s process, please see your syslog / log files"
                             " (and check if stopping apparmor helps, in case you use it)." % SLAPD_EXECUTABLE)
            ldap_env.load_directory(ldif_content=self.ldif_content)
            self.ldap_envs.append(ldap_env)

    def teardown_class(self):
        """ Stop slapd, remove LDAP server environment """
        for ldap_env in self.ldap_envs:
            try:
                ldap_env.stop_slapd()
            except:
                pass # one will fail, because it is already stopped
            ldap_env.destroy_env()

    def testMoinLDAPFailOver(self):
        """ Try if it does a failover to a secondary LDAP, if the primary fails. """
        handle_auth = self.request.handle_auth

        # authenticate user (with primary slapd):
        u1 = handle_login(self.request, None, username='usera', password='usera')
        assert u1 is not None
        assert u1.valid

        # now we kill our primary LDAP server:
        self.ldap_envs[0].slapd.stop()

        # try if we can still authenticate (with the second slapd):
        u2 = handle_login(self.request, None, username='usera', password='usera')
        assert u2 is not None
        assert u2.valid



