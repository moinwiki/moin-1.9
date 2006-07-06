#!/usr/bin/env python
"""
    Start script for the standalone Wiki server.

    @copyright: 2004-2005 Thomas Waldmann, Nir Soffer
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

from MoinMoin.server.standalone import StandaloneConfig, run


class Config(StandaloneConfig):

    # Server name
    # Used to create .log, .pid and .prof files
    name = 'moin'

    # Path to moin shared files (default '/usr/share/moin/wiki/htdocs')
    # If you installed with --prefix=PREFIX, use 'PREFIX/share/moin/wiki/htdocs'
    docs = '/usr/share/moin/htdocs'

    # The server will run with as this user and group (default 'www-data')
    user = 'www-data'
    group = 'www-data'

    # Port (default 8000)
    # To serve privileged port under 1024 you will have to run as root.
    port = 8000

    # Interface (default 'localhost')
    # The default will listen only to localhost.
    # '' will listen to any interface
    interface = 'localhost'

    # Log (default commented)
    # Log is written to stderr or to a file you specify here.
    ## logPath = name + '.log'

    # Server class (default ThreadPoolServer)
    # 'ThreadPoolServer' - create a constant pool of threads, simplified
    # Apache worker mpm.
    # 'ThreadingServer' - serve each request in a new thread. Much
    # slower for static files.
    # 'ForkingServer' - serve each request on a new child process -
    # experimental, slow.
    # 'SimpleServer' - server one request at a time. Fast, low
    # memory footprint.
    # If you set one of the threading servers and threads are not
    # available, the server will fallback to ForkingServer. If fork is
    # not available, the server will fallback to SimpleServer.
    serverClass = 'ThreadPoolServer'
    
    # Thread limit (default 10)
    # Limit the number of threads created. Ignored on non threaded servers.
    threadLimit = 10

    # Request queue size (default 50)
    # The size of the socket listen backlog.
    requestQueueSize = 50

    # Properties
    # Allow overriding any request property by the value defined in
    # this dict e.g properties = {'script_name': '/mywiki'}.
    properties = {}
    
    # Memory profile (default commented)
    # Useful only if you are a developer or interested in moin memory usage
    # A memory profile named 'moin--2004-09-27--01-24.log' is
    # created each time you start the server.
    ## from MoinMoin.util.profile import Profiler
    ## memoryProfile = Profiler(name, requestsPerSample=100, collect=0)

    # Hotshot profile (default commented)
    # Not compatible with threads - use with SimpleServer only.
    ## hotshotProfile = name + '.prof'


if __name__ == '__main__':
    run(Config)

