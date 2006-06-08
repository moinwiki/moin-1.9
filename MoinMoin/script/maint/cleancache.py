# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - cleancache script

    globally delete cache files in data/pages/PageName/cache/ directories
    
    You will usually do this after changing MoinMoin code, by either upgrading
    version, installing or removing macros. This often makes the text_html
    files invalid, so you have to remove them (the wiki will recreate them
    automatically).
    
    text_html is the name of the cache file used for compiled pages formatted
    by the wiki text to html formatter,

    @copyright: 2005-2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

cachefiles_to_delete = ['text_html', 'pagelinks', ]

import os

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
    
    def mainloop(self):
        self.init_request()
        base = self.request.cfg.data_dir
        pagesdir = os.path.join(base, 'pages')
        for f in os.listdir(pagesdir):
            for fname in cachefiles_to_delete:
                cachefile = os.path.join(pagesdir, f, 'cache', fname)
                try:
                    os.remove(cachefile)
                    print "Removed %s" % cachefile
                except:
                    pass

