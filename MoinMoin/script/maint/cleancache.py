# -*- coding: iso-8859-1 -*-
"""
MoinMoin - cleancache script

@copyright: 2005-2007 MoinMoin:ThomasWaldmann,
            2007-2009 MoinMoin:ReimarBauer
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin import caching, user
from MoinMoin.Page import Page
from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This script allows you to globally delete all the cache files in data/pages/PageName/cache/
and /data/cache directories

You will usually do this after changing MoinMoin code, by either upgrading
version, installing or removing macros or changing the regex expression for dicts.
This often makes the text_html and dict files invalid, so you have to remove them
(the wiki will recreate them automatically).

text_html is the name of the cache file used for compiled pages formatted
by the wiki text to html formatter, A dict file does cache the pages which
do fit to the page_group_regex variable.

Detailed Instructions:
======================
General syntax: moin [options] maint cleancache

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def mainloop(self):
        self.init_request()
        request = self.request

        # clean page scope cache entries
        keys = ['text_html', 'pagelinks', 'hitcounts', ]
        pages = request.rootpage.getPageList(user='')
        for pagename in pages:
            arena = Page(request, pagename)
            for key in keys:
                caching.CacheEntry(request, arena, key, scope='item').remove()

        # clean wiki scope cache entries
        arena_key_list = [
            ('charts', 'hitcounts'),
            ('charts', 'pagehits'),
            ('charts', 'useragents'),
            ('user', 'name2id'),
            ('wikidicts', 'dicts_groups'),
        ]
        for arena, key in arena_key_list:
            caching.CacheEntry(request, arena, key, scope='wiki').remove()

        # clean drafts of users
        uids = user.getUserList(request)
        for key in uids:
            caching.CacheEntry(request, 'drafts', key, scope='wiki').remove()
