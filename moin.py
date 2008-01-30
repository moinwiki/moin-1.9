#!/usr/bin/env python
"""
    Start script for the standalone Wiki server.

    @copyright: 2007 MoinMoin:ForrestVoight
    @license: GNU GPL, see COPYING for details.
"""

import sys
import os

from MoinMoin.script import MoinScript

# Path to MoinMoin package, needed if you installed with --prefix=PREFIX
# or if you did not use setup.py.
#sys.path.insert(0, 'PREFIX/lib/python2.3/site-packages')

moinpath = os.path.abspath(os.path.normpath(os.path.dirname(sys.argv[0])))
sys.path.insert(0, moinpath)
os.chdir(moinpath)

if __name__ == '__main__':
    sys.argv = ["moin.py", "server", "standalone"]
    MoinScript().run()
