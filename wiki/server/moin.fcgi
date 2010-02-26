#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    MoinMoin - CGI/FCGI Driver script

    @copyright: 2000-2005 by Juergen Hermann <jh@web.de>,
                2008 by MoinMoin:ThomasWaldmann,
                2008 by MoinMoin:FlorianKrupicka,
                2010 by MoinMoin:RadomirDopieralski
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
from MoinMoin import log
#log.load_config('/path/to/logging_configuration_file')
logging = log.getLogger(__name__)

## this works around a bug in flup's CGI autodetection (as of flup 1.0.1):
#os.environ['FCGI_FORCE_CGI'] = 'Y' # 'Y' for (slow) CGI, 'N' for FCGI

# Creating the WSGI application
# use shared=True to have moin serve the builtin static docs
# use shared=False to not have moin serve static docs
# use shared='/my/path/to/htdocs' to serve static docs from that path
from MoinMoin.web.serving import make_application
app = make_application(shared=True)  # <-- adapt here as needed

# Is fixing the script name needed?
# Use None if your url looks like http://domain/wiki/moin.fcgi
# Use '' if you use rewriting to run at http://domain/
# Use '/mywiki' if you use rewriting to run at http://domain/mywiki/
fix_script_name = None  # <-- adapt here as needed

if fix_script_name is None:
    application = app
else:
    def script_name_fixer(env, start):
        env['SCRIPT_NAME'] = fix_script_name
        return app(env, start)
    application = script_name_fixer


# CGI with Apache2 on Windows (maybe other combinations also) has trouble with
# URLs of non-ASCII pagenames. Use True to enable middleware that tries to fix.
fix_apache_win32 = False  # <-- adapt here as needed

if fix_apache_win32:
    from werkzeug.contrib.fixers import PathInfoFromRequestUriFix
    application = PathInfoFromRequestUriFix(application)


## Choose your server mode (threaded, forking or single-thread)
try:
    # v-- adapt here as needed
    from flup.server.fcgi import WSGIServer
#    from flup.server.fcgi_fork import WSGIServer
#    from flup.server.fcgi_single import WSGIServer
except ImportError:
    logging.warning("No flup-package installed, only basic CGI support is available.")
    from MoinMoin.web._fallback_cgi import WSGIServer

WSGIServer(application).run()

