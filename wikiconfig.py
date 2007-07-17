# -*- coding: iso-8859-1 -*-
"""MoinMoin Desktop Edition (MMDE) - Configuration

ONLY to be used for MMDE - if you run a personal wiki on your notebook or PC.

This is NOT intended for internet or server or multiuser use due to relaxed security settings!
"""
import sys, os
from MoinMoin.config.multiconfig import DefaultConfig


class Config(DefaultConfig):
    # vvv DON'T TOUCH THIS EXCEPT IF YOU KNOW WHAT YOU DO vvv
    moinmoin_dir = os.path.abspath(os.path.normpath(os.path.dirname(sys.argv[0])))
    data_dir = os.path.join(moinmoin_dir, 'wiki', 'data')
    data_underlay_dir = os.path.join(moinmoin_dir, 'wiki', 'underlay')

    DesktopEdition = True # give all local users full powers
    acl_rights_default = u"All:read,write,delete,revert,admin"
    surge_action_limits = None # no surge protection
    sitename = u'MoinMoin DesktopEdition'
    logo_string = u'<img src="/moin_static170/common/moinmoin.png" alt="MoinMoin Logo">'
    page_front_page = u'FrontPage' # change to some better value
    page_credits = [
        '<a href="http://moinmoin.wikiwikiweb.de/">MoinMoin DesktopEdition Powered</a>',
        '<a href="http://www.python.org/">Python Powered</a>',
    ]
    # ^^^ DON'T TOUCH THIS EXCEPT IF YOU KNOW WHAT YOU DO ^^^

    # developers, add your testing config values in this file
    # (and don't add it to your repository):
    try:
        from wikiconfig_local import *
    except ImportError:
        pass
