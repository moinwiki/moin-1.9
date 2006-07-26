# -*- coding: iso-8859-1 -*-
"""
MoinMoin - test wiki configuration

@copyright: 2000-2004 by Juergen Hermann <jh@web.de>
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.config.multiconfig import DefaultConfig


class Config(DefaultConfig):
    sitename = u'Developer Test Wiki'
    logo_string = sitename
    data_dir = './testwiki/data/'
    data_underlay_dir = './testwiki/underlay/'
    show_hosts = 1                  
    # used to check if it is really a wiki we may modify 
    is_test_wiki = True

