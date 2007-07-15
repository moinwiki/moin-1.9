"""
Verify that the MoinMoin source files conform (mostly) to PEP8 coding style.

Additionally, we check that the files have no crlf (Windows style) line endings.

@copyright: 2006 by Armin Rigo (originally only testing for tab chars),
            2007 adapted and extended (calling the PEP8 checker for most stuff) by MoinMoin:ThomasWaldmann.
@license: MIT licensed
"""

import os, re

import pep8

from MoinMoin.conftest import moindir

ROOT = str(moindir)

EXCLUDE = [
    '/contrib/DesktopEdition/setup_py2exe.py', # has crlf
    '/contrib/TWikiDrawPlugin', # 3rd party java stuff
    '/MoinMoin/support', # 3rd party libs or non-broken stdlib stuff
    '/wiki/htdocs/applets/FCKeditor', # 3rd party GUI editor
    '/tests/wiki', # this is our test wiki
    '/wiki/htdocs', # this is our dist static stuff
]

TRAILING_SPACES = 'nochange' # 'nochange' or 'fix'
                             # use 'fix' with extreme caution and in a separate changeset!
FIX_TS_RE = re.compile(r' +$', re.M) # 'fix' mode: everything matching the trailing space re will be removed


def pep8_error_count(path):
    # process_options initializes some data structures and MUST be called before each Checker().check_all()
    pep8.process_options(['pep8', '--ignore=E202,E221,E222,E241,E301,E302,E401,E501,E701,W391,W601,W602', '--show-source', 'dummy_path'])
    error_count = pep8.Checker(path).check_all()
    return error_count

def check_py_file(reldir, path):
    if TRAILING_SPACES == 'fix':
        f = file(path, 'rb')
        data = f.read()
        f.close()
        data = FIX_TS_RE.sub('', data)
        f = file(path, 'wb')
        f.write(data)
        f.close()
    # Please read and follow PEP8 - rerun this test until it does not fail any more,
    # any type of error is only reported ONCE (even if there are multiple).
    error_count = pep8_error_count(path)
    assert error_count == 0

def test_sourcecode():
    def walk(reldir):
        if reldir in EXCLUDE:
            #print "Skippping %r..." % reldir
            return
        if reldir:
            path = os.path.join(ROOT, *reldir.split('/'))
        else:
            path = ROOT
        if os.path.isfile(path):
            if path.lower().endswith('.py'):
                yield check_py_file, reldir, path
        elif os.path.isdir(path):
            for entry in os.listdir(path):
                if not entry.startswith('.'):
                    for _ in walk('%s/%s' % (reldir, entry)):
                        yield _

    global EXCLUDE
    EXCLUDE = dict([(path, True) for path in EXCLUDE]) # dict lookup is faster
    for _ in walk(''):
        yield _

