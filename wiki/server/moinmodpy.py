# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - mod_python wrapper for broken mod_python versions

    add a .htaccess to the path below which you want to have your
    wiki instance:

    <Files wiki>
      SetHandler python-program
      PythonPath "['/path/to/share/moin/server'] + sys.path"
      PythonHandler moinmodpy
    </Files>

    Note: this is a wrapper needed because of a bug in
          mod_python < 3.1.3


    mod_python.apache.resolve_object fails to parse a object with dots.

    If you have a newer version, take a look at moinmodpy.htaccess
    to see how to use MoinMoin without this wrapper. You can also
    look into INSTALL.html to see how you can fix the bug on your own
    (a simple one line change).

    @copyright: 2004-2005 by Oliver Graf <ograf@bitart.de>
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

# Debug mode - show detailed error reports
#os.environ['MOIN_DEBUG'] = '1'

from MoinMoin.server.server_modpython import ModpythonConfig, modpythonHandler


class MyConfig(ModpythonConfig):
    """ Set up local server-specific stuff here """
    # Properties
    # Allow overriding any request property by the value defined in
    # this dict e.g properties = {'script_name': '/mywiki'}.
    ## properties = {}

def handler(request):
    return modpythonHandler(request, MyConfig)

