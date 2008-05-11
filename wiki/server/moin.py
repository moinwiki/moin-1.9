#!/usr/bin/env python
"""
    Start script for the standalone Wiki server.

    @copyright: 2007 MoinMoin:ForrestVoight,
                2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, sys

# Path to MoinMoin package, needed if you installed with --prefix=PREFIX
# or if you did not use setup.py.
#sys.path.insert(0, 'PREFIX/lib/python2.3/site-packages')

moinpath = os.path.abspath(os.path.normpath(os.path.dirname(sys.argv[0])))
sys.path.insert(0, moinpath)
os.chdir(moinpath)

from MoinMoin import log
log.load_config('wiki/config/logging/stderr') # XXX please fix this path!

from MoinMoin.script import MoinScript

if __name__ == '__main__':
    sys.argv = ["moin.py", "server", "standalone"]
    MoinScript().run()
