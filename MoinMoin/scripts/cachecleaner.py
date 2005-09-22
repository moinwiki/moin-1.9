#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - clear the cache

    @copyright: 2005 by Thomas Waldmann (MoinMoin:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details.

    globally delete cache files in data/pages/PageName/cache/ directories
    
    Usage:
    First change the base path and fname to match your needs.
    Then do ./cachecleaner.py

    You will usually do this after changing MoinMoin code, by either upgrading
    version, installing or removing macros. This often makes the text_html
    files invalid, so you have to remove them (the wiki will recreate them
    automatically).
    
    text_html is the name of the cache file used for compiled pages formatted
    by the wiki text to html formatter,
"""

base = "." # location of data directory
fname = 'text_html' # cache filename to delete

import sys, os

pagesdir = os.path.join(base,'data','pages')
for f in os.listdir(pagesdir):
    cachefile = os.path.join(pagesdir,f,'cache',fname)
    try:
        os.remove(cachefile)
    except:
        pass
    
# EOF

