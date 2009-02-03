# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - http authentication (or rather: using REMOTE_USER)

    This is just a dummy redirecting to MoinMoin.auth.GivenAuth for backwards
    compatibility.
    
    Please fix your setup, this dummy will be removed soon:

    Old (1.8.x):
    ------------
    from MoinMoin.auth.http import HTTPAuth
    auth = [HTTPAuth(autocreate=True)]
    # any presence (or absence) of 'http' auth name, e.g.:
    auth_methods_trusted = ['http', 'xmlrpc_applytoken']

    New (1.9.x):
    ------------
    from MoinMoin.auth import GivenAuth
    auth = [GivenAuth(autocreate=True)]
    # presence (or absence) of 'given' auth name, e.g.:
    auth_methods_trusted = ['given', 'xmlrpc_applytoken']

    @copyright: 2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.auth import GivenAuth

class HTTPAuth(GivenAuth):
    name = 'http'  # GivenAuth uses 'given'
    logging.warning("DEPRECATED use of MoinMoin.auth.http, please read instructions there or docs/CHANGES!")

