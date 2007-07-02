"""
Verify that the MoinMoin source files
 * have no tabs,
 * end with \n,
 * have no crlf (Windows style) line endings,
 * have no trailing spaces at line endings.

@copyright: 2006 by Armin Rigo,
            2007 adapted and extended for MoinMoin by MoinMoin:ThomasWaldmann.
@license: MIT licensed
"""

import os, re

from MoinMoin.conftest import moindir

ROOT = str(moindir)

EXCLUDE = [
    '/contrib/DesktopEdition/setup_py2exe.py', # has crlf
    '/MoinMoin/support', # 3rd party libs or non-broken stdlib stuff
    '/wiki/htdocs/applets/FCKeditor', # 3rd party GUI editor
]

TRAILING_SPACES = 'ignore' # 'ignore', 'test' or 'fix'
                           # use 'fix' with extreme caution and in a separate changeset!
FIX_TS_RE = re.compile(r' +$', re.M) # 'fix' mode: everything matching the trailing space re will be removed

PEP8_CHECKS = True

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
                f = file(path, 'rb')
                data = f.read()
                f.close()
                assert '\t' not in data, "%r contains tabs (please use 4 space chars for indenting)!" % (reldir,)
                assert not data or data.endswith('\n'), "%r does not end with a newline char!" % (reldir,)
                assert '\r\n' not in data, "%r contains crlf line endings (please use UNIX style, lf only)!" % (reldir,)
                if TRAILING_SPACES != 'ignore':
                    if TRAILING_SPACES == 'test':
                        assert ' \n' not in data, "%r contains line(s) with trailing spaces!" % (reldir,)
                    elif TRAILING_SPACES == 'fix':
                        data = FIX_TS_RE.sub('', data)
                        f = file(path, 'wb')
                        f.write(data)
                        f.close()
                if PEP8_CHECKS:
                    # Please read and follow PEP8 - rerun this test until it does not fail any more,
                    # any type of error is only reported ONCE (even if there are multiple).
                    assert pep8_error_count(path) == 0
        elif os.path.isdir(path):
            for entry in os.listdir(path):
                if not entry.startswith('.'):
                    walk('%s/%s' % (reldir, entry))

    global EXCLUDE
    EXCLUDE = dict([(path, True) for path in EXCLUDE]) # dict lookup is faster
    walk('')

import pep8
pep8.process_options(['pep8', '--ignore=E302,E401,E501,E701,W', 'dummy_path'])
#pep8.process_options(['pep8', path])

def pep8_error_count(path):
    error_count = pep8.Checker(path).check_all()
    return error_count

