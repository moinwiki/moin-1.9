#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - CGI/FCGI Driver script

    @copyright: 2000-2005 by Juergen Hermann <jh@web.de>,
                2008 by MoinMoin:ThomasWaldmann,
                2008 by MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

import sys, os

# a) Configuration of Python's code search path
#    If you already have set up the PYTHONPATH environment variable for the
#    stuff you see below, you don't need to do a1) and a2).

# a1) Path of the directory where the MoinMoin code package is located.
#     Needed if you installed with --prefix=PREFIX or you didn't use setup.py.
#sys.path.insert(0, 'PREFIX/lib/python2.3/site-packages')

# a2) Path of the directory where wikiconfig.py / farmconfig.py is located.
#     See wiki/config/... for some sample config files.
#sys.path.insert(0, '/path/to/wikiconfigdir')
#sys.path.insert(0, '/path/to/farmconfigdir')

# b) Configuration of moin's logging
#    If you have set up MOINLOGGINGCONF environment variable, you don't need this!
#    You also don't need this if you are happy with the builtin defaults.
#    See wiki/config/logging/... for some sample config files.
#from MoinMoin import log
#log.load_config('/path/to/logging_configuration_file')

# this works around a bug in flup's CGI autodetection (as of flup 1.0.1):
os.environ['FCGI_FORCE_CGI'] = 'Y' # 'Y' for (slow) CGI, 'N' for FCGI

from MoinMoin.web.flup_frontend import CGIFrontEnd
CGIFrontEnd().run()

