# -*- coding: iso-8859-1 -*-
"""
MoinMoin - makecache script

@copyright: 2008 MoinMoin:ReimarBauer
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin import caching
from MoinMoin.Page import Page
from MoinMoin.script import MoinScript
from MoinMoin.stats import hitcounts

class PluginScript(MoinScript):
    """\
Purpose:
========
This script allows you to create cache files in data/pages/PageName/cache/
and /data/cache directories

You will usually do this after changing MoinMoin code and calling "maint cleancache", by either upgrading
version, installing or removing macros or changing the regex expression for dicts.

text_html is the name of the cache file used for compiled pages formatted
by the wiki text to html formatter, A dict file does cache the pages which
do fit to the page_group_regex variable.

Detailed Instructions:
======================
General syntax: moin [options] maint makecache

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def mainloop(self):
        self.init_request()
        request = self.request

        # make cache related to pagelinks entries of a page
        pages = request.rootpage.getPageList(user='', exists=1)
        for pagename in pages:
            page = Page(request, pagename)
            request.page = page
            p = page.getPageLinks(request)

