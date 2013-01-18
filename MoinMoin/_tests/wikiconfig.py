# -*- coding: iso-8859-1 -*-
"""
MoinMoin - test wiki configuration

Do not change any values without good reason.

We mostly want to have default values here, except for stuff that doesn't
work without setting them (like data_dir and underlay_dir).

@copyright: 2000-2004 by Juergen Hermann <jh@web.de>
@license: GNU GPL, see COPYING for details.
"""

import os

from MoinMoin.config.multiconfig import DefaultConfig


class Config(DefaultConfig):
    sitename = u'Developer Test Wiki'
    logo_string = sitename

    _base_dir = os.path.join(os.path.dirname(__file__), '../../tests/wiki')
    data_dir = os.path.join(_base_dir, "data")
    data_underlay_dir = os.path.join(_base_dir, "underlay")

    #show_hosts = 1

    #secrets = 'some not secret string just to make tests happy'

    # used to check if it is really a wiki we may modify
    is_test_wiki = True

    # for runnging tests without passlib support:
    #passlib_support = False
    #password_scheme = '{SSHA}'

    # for running tests with passlib support:
    passlib_crypt_context = dict(
        schemes=["sha512_crypt", ],
        # for the tests, we don't want to have varying rounds
        sha512_crypt__vary_rounds=0,
        # for the tests, we want to have a rather low rounds count,
        # so the tests run quickly (do NOT use low counts in production!)
        sha512_crypt__default_rounds=1001,
    )

