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
    '/contrib/DesktopEdition/setup_py2exe.py', # has crlf
    '/MoinMoin/support', # 3rd party libs or non-broken stdlib stuff
    '/wiki/htdocs/applets/FCKeditor', # 3rd party GUI editor
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
                assert '\t' not in data, "%r contains tabs (please use 4 space chars for indenting)!" % (reldir,)
                assert not data or data.endswith('\n'), "%r does not end with a newline char!" % (reldir,)
                assert '\r\n' not in data, "%r contains crlf line endings (please use UNIX style, lf only)!" % (reldir,)
        elif os.path.isdir(path):
            for entry in os.listdir(path):
                if not entry.startswith('.'):
                    walk('%s/%s' % (reldir, entry))

    global EXCLUDE
    EXCLUDE = dict([(path, True) for path in EXCLUDE]) # dict lookup is faster
    walk('')

