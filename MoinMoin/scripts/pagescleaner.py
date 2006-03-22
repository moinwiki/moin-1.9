#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - display unused or trash page directories in data/pages
    
    Usage:
    First change the base path to match your needs.
    Then do ./pagescleaner.py >cleanthem.sh
    Then please review cleanthem.sh and run it, if it is OK.

    @copyright: 2005 by Thomas Waldmann (MoinMoin:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details.
"""

import os

base = "."
pagebasedir = base + "/data/pages"

def qualify(p):
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
            curr = int(current)
        except:
            return 'current damaged'
        if current not in revs:
            return 'deleted'
    else:
        return 'no current'

    return 'ok'

def run():
    for p in os.listdir(pagebasedir):
        pagedir = os.path.join(pagebasedir, p)
        status = qualify(pagedir)
        if status in ['trash', 'empty', ]:
            print "mv '%s' trash # %s" % (pagedir,status)
        elif status in ['deleted', ]:
            print "mv '%s' deleted # %s" % (pagedir,status)
        else:
            print "# %s: '%s'" % (status, pagedir)

if __name__ == "__main__":
    run()

