# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - cleancache script

    globally delete cache files in data/pages/PageName/cache/ and /data/cache directories

    You will usually do this after changing MoinMoin code, by either upgrading
    version, installing or removing macros or changing the regex expression for dicts.
    This often makes the text_html and dict files invalid, so you have to remove them
    (the wiki will recreate them automatically).

    text_html is the name of the cache file used for compiled pages formatted
    by the wiki text to html formatter, A dict file does cache the pages which
    do fit to the page_group_regex variable.

    @copyright: 2005-2006 MoinMoin:ThomasWaldmann
                2007 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

import os
from MoinMoin import caching
from MoinMoin.Page import Page
from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def mainloop(self):
        self.init_request()
        request = self.request

        key = 'text_html'
        pages = request.rootpage.getPageList(user='')

        for pagename in pages:
            arena = Page(request, pagename)
            caching.CacheEntry(request, arena, key, scope='item').remove()
            caching.CacheEntry(request, arena, "pagelinks", scope='item').remove()

        # cleans the name2id
        caching.CacheEntry(request, 'user', 'name2id', scope='wiki').remove()
        # cleans the wikidicts
        caching.CacheEntry(request, 'wikidicts', 'dicts_groups', scope='wiki').remove()
        # cleans i18n meta
        caching.CacheEntry(request, 'i18n', 'meta', scope='wiki').remove()

