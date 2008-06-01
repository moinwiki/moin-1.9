# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.auth.ldap Tests

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import ldap

import py.test

from MoinMoin._tests.ldap_testbase import LDAPTestBase, LdapEnvironment
from MoinMoin._tests.ldap_testdata import *

class TestSimpleLdap(LDAPTestBase):
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

    def testMoinLDAPLogin(self):
        """ Just try accessing the LDAP server and see if usera and userb are in LDAP. """
        server_uri = self.ldap_env.slapd.url
        base_dn = self.ldap_env.basedn

        from MoinMoin.auth.ldap_login import LDAPAuth
        ldap_auth1 = LDAPAuth(server_uri=server_uri, base_dn=base_dn)
        self.config = self.TestConfig(auth=[ldap_auth1, ], user_autocreate=True)
        handle_auth = self.request.handle_auth

        # tests that must not authenticate:
        u = handle_auth(None, username='', password='', login=True)
        assert u is None
        u = handle_auth(None, username='usera', password='', login=True)
        assert u is None
        u = handle_auth(None, username='usera', password='userawrong', login=True)
        assert u is None
        u = handle_auth(None, username='userawrong', password='usera', login=True)
        assert u is None

        # tests that must authenticate:
        u1 = handle_auth(None, username='usera', password='usera', login=True)
        assert u1 is not None
        assert u1.valid

        u2 = handle_auth(None, username='userb', password='userb', login=True)
        assert u2 is not None
        assert u2.valid

        # check if usera and userb have different ids:
        assert u1.id != u2.id

class TestComplexLdap:
    basedn = BASEDN
    rootdn = ROOTDN
    rootpw = ROOTPW
    slapd_config = SLAPD_CONFIG
    ldif_content = LDIF_CONTENT

    def setup_class(self):
        """ Create LDAP servers environment, start slapds """
        py.test.skip("Failover not implemented yet")
        self.ldap_envs = []
        for instance in range(2):
            ldap_env = LdapEnvironment(self.basedn, self.rootdn, self.rootpw, instance=instance)
            ldap_env.create_env(slapd_config=self.slapd_config)
            ldap_env.start_slapd()
            ldap_env.load_directory(ldif_content=self.ldif_content)
            self.ldap_envs.append(ldap_env)

    def teardown_class(self):
        """ Stop slapd, remove LDAP server environment """
        py.test.skip("Failover not implemented yet")
        for ldap_env in self.ldap_envs:
            try:
                ldap_env.stop_slapd()
            except:
                pass # one will fail, because it is already stopped
            ldap_env.destroy_env()

    def testLDAP(self):
        """ Just try accessing the LDAP servers and see if usera and userb are in LDAP. """
        py.test.skip("Failover not implemented yet")
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

    def testMoinLDAPLogin(self):
        """ Just try accessing the LDAP server and see if usera and userb are in LDAP. """
        py.test.skip("Failover not implemented yet")
        from MoinMoin.auth.ldap_login import LDAPAuth
        authlist = []
        for ldap_env in self.ldap_envs:
            server_uri = ldap_env.slapd.url
            base_dn = ldap_env.basedn
            ldap_auth = LDAPAuth(server_uri=server_uri, base_dn=base_dn)
            authlist.append(ldap_auth)

        self.config = self.TestConfig(auth=authlist, user_autocreate=True)
        handle_auth = self.request.handle_auth

        # authenticate user (with primary slapd):
        u1 = handle_auth(None, username='usera', password='usera', login=True)
        assert u1 is not None
        assert u1.valid

        # now we kill our primary LDAP server:
        self.ldap_envs[0].slapd.stop()

        # try if we can still authenticate (with the second slapd):
        u2 = handle_auth(None, username='usera', password='usera', login=True)
        assert u2 is not None
        assert u2.valid


