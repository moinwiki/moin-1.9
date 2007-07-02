"""
Verify that the MoinMoin source files
 * have no tabs,
 * end with \n,
 * have no crlf (Windows style) line endings,
 * have no trailing spaces at line endings (test currently disabled).
 
@copyright: 2006 by Armin Rigo,
            2007 adapted and extended for MoinMoin by MoinMoin:ThomasWaldmann.
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

def test_sourcecode():
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
                #triggers too often currently, developers please clean up your src files!
                #assert ' \n' not in data, "%r contains line(s) with trailing spaces!" % (reldir,)
        elif os.path.isdir(path):
            for entry in os.listdir(path):
                if not entry.startswith('.'):
                    walk('%s/%s' % (reldir, entry))

    global EXCLUDE
    EXCLUDE = dict([(path, True) for path in EXCLUDE]) # dict lookup is faster
    walk('')

