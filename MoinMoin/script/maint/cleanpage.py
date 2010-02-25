# -*- coding: iso-8859-1 -*-
"""
MoinMoin - display unused or trash page directories in data/pages

@copyright: 2005-2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

import os

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool outputs a shell script which upon execution will remove unused or
trashed pages from the wiki.

Detailed Instructions:
======================
General syntax: moin [options] maint cleanpage [cleanpage-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[cleanpage-options] see below:
    0. Verify the outputted shell script before running it.

    1. This script takes no command line arguments.
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def qualify(self, p):
        """ look at page directory p and return its state """
        dir = os.listdir(p)
        if not dir:
            return 'empty'

        # check if we have something of potential value
        revs = []
        if 'revisions' in dir:
            revs = os.listdir(os.path.join(p, 'revisions'))
        atts = []
        if 'attachments' in dir:
            atts = os.listdir(os.path.join(p, 'attachments'))

        if not revs and not atts:
            return 'trash'

        if 'current-locked' in dir:
            return 'current-locked'
        elif 'current' in dir:
            try:
                current = open(os.path.join(p, 'current')).read().strip()
                int(current)
            except:
                return 'current damaged'
            if current not in revs:
                return 'deleted'
        else:
            return 'no current'

        return 'ok'

    def mainloop(self):
        self.init_request()
        base = self.request.cfg.data_dir
        pagesdir = os.path.join(base, 'pages')
        for p in os.listdir(pagesdir):
            pagedir = os.path.join(pagesdir, p)
            status = self.qualify(pagedir)
            if status in ['trash', 'empty', ]:
                print "mv '%s' trash # %s" % (pagedir, status)
            elif status in ['deleted', ]:
                print "mv '%s' deleted # %s" % (pagedir, status)
            else:
                print "# %s: '%s'" % (status, pagedir)

