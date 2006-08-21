#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI Driver Script

    @copyright: 2000-2005 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# System path configuration

import sys

# Path of the directory where wikiconfig.py is located.
# YOU NEED TO CHANGE THIS TO MATCH YOUR SETUP.
sys.path.insert(0, '/path/to/wikiconfig')

# Path to MoinMoin package, needed if you installed with --prefix=PREFIX
# or if you did not use setup.py.
## sys.path.insert(0, 'PREFIX/lib/python2.3/site-packages')

# Path of the directory where farmconfig.py is located (if different).
## sys.path.insert(0, '/path/to/farmconfig')

# Debug mode - show detailed error reports
## import os
## os.environ['MOIN_DEBUG'] = '1'

# This is used to profile MoinMoin (default disabled)
hotshotProfiler = 0

# ---------------------------------------------------------------------

if hotshotProfiler:
    import hotshot
    prof = hotshot.Profile("moin.prof")
    prof.start()

from MoinMoin.request import CGI
request = CGI.Request()
request.run()

if hotshotProfiler:
    prof.close()

