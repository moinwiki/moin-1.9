# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - mod_python wrapper for broken mod_python versions

    add a .htaccess to the path below which you want to have your
    wiki instance:

    <Files wiki>
      SetHandler python-program
      PythonPath "['/path/to/moin/share/moin/cgi-bin'] + sys.path"
      PythonHandler moinmodpy
    </Files>

    Note: this is a wrapper needed because of a bug in
          mod_python < 3.1.3


    mod_python.apache.resolve_object fails to parse a object with dots.

    If you have a newer version, take a look at moinmodpy.htaccess
    to see how to use MoinMoin without this wrapper. You can also
    look into INSTALL.html to see how you can fix the bug on your own
    (a simple one line change).

    TODO: this should be refactored so it uses MoinMoin.server package
          (see how server_twisted, server_wsgi and server_standalone use it)

    @copyright: 2004-2005 by Oliver Graf <ograf@bitart.de>
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

# Path of the directory where farmconfig is located (if different).
## sys.path.insert(0, '/path/to/farmconfig')

# Debug mode - show detailed error reports
## import os
## os.environ['MOIN_DEBUG'] = '1'

from MoinMoin import log
log.load_config('wiki/config/logging/conffile') # XXX please fix this path!

# Simple way
#from MoinMoin.server.server_modpython import modpythonHandler as handler

# Complex way
from MoinMoin.server.server_modpython import ModpythonConfig, modpythonHandler

class MyConfig(ModpythonConfig):
    """ Set up local server-specific stuff here """
    # Properties
    # Allow overriding any request property by the value defined in
    # this dict e.g properties = {'script_name': '/mywiki'}.
    ## properties = {}

def handler(request):
    return modpythonHandler(request, MyConfig)

