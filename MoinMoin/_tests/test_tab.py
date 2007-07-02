"""
Verify that the MoinMoin source files have no tabs.

@copyright: 2006 by Armin Rigo,
            2007 adapted for MoinMoin by MoinMoin:ThomasWaldmann.
@license: MIT licensed
"""

import os

from MoinMoin.conftest import moindir

ROOT = str(moindir)

EXCLUDE = [
    '/MoinMoin/parser',
    '/MoinMoin/formatter',
    '/wiki/htdocs/applets/FCKeditor',
]

def test_no_tabs():
    def walk(reldir):
        if reldir in EXCLUDE:
            return
        if reldir:
            path = os.path.join(ROOT, *reldir.split('/'))
        else:
            path = ROOT
        if os.path.isfile(path):
            if path.lower().endswith('.py'):
                f = open(path, 'r')
                data = f.read()
                f.close()
                assert '\t' not in data, "%r contains tabs!" % (reldir,)
        elif os.path.isdir(path):
            for entry in os.listdir(path):
                if not entry.startswith('.'):
                    walk('%s/%s' % (reldir, entry))

    global EXCLUDE
    EXCLUDE = dict([(path, True) for path in EXCLUDE]) # dict lookup is faster
    walk('')

