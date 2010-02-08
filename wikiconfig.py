# -*- coding: iso-8859-1 -*-
"""MoinMoin Desktop Edition (MMDE) - Configuration

ONLY to be used for MMDE - if you run a personal wiki on your notebook or PC.

This is NOT intended for internet or server or multiuser use due to relaxed security settings!
"""
import sys, os
from MoinMoin.config.multiconfig import DefaultConfig


class LocalConfig(DefaultConfig):
    # vvv DON'T TOUCH THIS EXCEPT IF YOU KNOW WHAT YOU DO vvv
    moinmoin_dir = os.path.abspath(os.path.normpath(os.path.dirname(sys.argv[0])))
    data_dir = os.path.join(moinmoin_dir, 'wiki', 'data')
    data_underlay_dir = os.path.join(moinmoin_dir, 'wiki', 'underlay')

    DesktopEdition = True # give all local users full powers
    acl_rights_default = u"All:read,write,delete,revert,admin"
    surge_action_limits = None # no surge protection
    sitename = u'MoinMoin DesktopEdition'
    logo_string = u'<img src="/moin_static187/common/moinmoin.png" alt="MoinMoin Logo">'
    page_front_page = u'FrontPage' # change to some better value
    # ^^^ DON'T TOUCH THIS EXCEPT IF YOU KNOW WHAT YOU DO ^^^

    # Add your configuration items here.
    secrets = 'This string is NOT a secret, please make up your own, long, random secret string!'


# DEVELOPERS! Do not add your configuration items there,
# you could accidentally commit them! Instead, create a
# wikiconfig_local.py file containing this:
#
# from wikiconfig import LocalConfig
#
# class Config(LocalConfig):
#     configuration_item_1 = 'value1'
#

try:
    from wikiconfig_local import Config
except ImportError, err:
    if not str(err).endswith('wikiconfig_local'):
        raise
    Config = LocalConfig
