"""
    MoinMoin - Moin as WSGI application with flup as fcgi gateway

    @copyright: 2005 by Anakim Border <akborder@gmail.com>,
                2008 by MoinMoin:ThomasWaldmann
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

use_threads = True
unixSocketPath = '/tmp/moin.sock'

# Set threads flag, so other code can use proper locking
from MoinMoin import config
config.use_threads = use_threads
del config

from flup.server.fcgi import WSGIServer
from MoinMoin.server.server_wsgi import moinmoinApp, WsgiConfig

class Config(WsgiConfig):
    pass

config = Config()

if __name__ == '__main__':
    server = WSGIServer(moinmoinApp, bindAddress=unixSocketPath)
    server.run()
    os.unlink(unixSocketPath)

