# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - mod_wsgi driver script

    To use this, add those statements to your Apache's VirtualHost definition:
    
    # this is for icons, css, js (and must match url_prefix from wiki config):
    Alias       /moin_static184/ /usr/share/moin/htdocs/

    # this is the URL http://servername/moin/ you will use later to invoke moin:
    WSGIScriptAlias /moin/ /some/path/moin.wsgi

    # create some wsgi daemons - use someuser.somegroup same as your data_dir:
    WSGIDaemonProcess daemonname user=someuser group=somegroup processes=5 threads=10 maximum-requests=1000
    # umask=0007 does not work for mod_wsgi 1.0rc1, but will work later

    # use the daemons we defined above to process requests!
    WSGIProcessGroup daemonname

    @copyright: 2008 by MoinMoin:ThomasWaldmann
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


from MoinMoin.server.server_wsgi import WsgiConfig, moinmoinApp

class Config(WsgiConfig):
    pass

config = Config()

application = moinmoinApp

