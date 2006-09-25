"""
    twisted.web based wiki server

    Run this server with mointwisted script on Linux or Mac OS X, or
    mointwisted.cmd on Windows.
    
    @copyright: 2004-2005 Thomas Waldmann, Oliver Graf, Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

# System path configuration

import sys

# Path of the directory where wikiconfig.py is located.
# YOU NEED TO CHANGE THIS TO MATCH YOUR SETUP.
sys.path.insert(0, '/path/to/wikiconfig')

# Path to MoinMoin package, needed if you installed with --prefix=PREFIX
# or if you did not use setup.py
## sys.path.insert(0, 'PREFIX/lib/python2.3/site-packages')

# Path to the directory where farmconfig is located (if different).
## sys.path.insert(0, '/path/to/farmconfig')

# Debug mode - show detailed error reports
## import os
## os.environ['MOIN_DEBUG'] = '1'

from MoinMoin.server.twistedmoin import TwistedConfig, makeApp


class Config(TwistedConfig):

    # Server name
    # Used to create .log, .pid and .prof files
    name = 'mointwisted'

    # Path to moin shared files (default '/usr/share/moin/wiki/htdocs')
    docs = '/usr/share/moin/htdocs'

    # URL prefix for the static stuff (used to access stuff in docs) - you
    # usually should not need to change this because Twisted moin uses
    # matching defaults for here and for wikiconfig.py:
    #url_prefix_static = '/moin_static160'

    # The server will run with as this user and group (default 'www-data')
    user = 'www-data'
    group = 'www-data'

    # Port (default 8080)
    # To serve privileged port under 1024 you will have to run as root
    port = 8080

    # Interfaces (default [''])
    # The interfaces the server will listen to. 
    # [''] - listen to all interfaces defined on the server
    # ['red.wikicolors.org', 'blue.wikicolors.org'] - listen to some
    # If '' is in the list, other ignored.
    interfaces = ['']

    # How many threads to use (default 10, max 20)
    # The more threads you use, the more memory moin uses. All thread
    # use one CPU, and will not run faster, but might be more responsive
    # on a very busy server.
    threads = 10

    # Set logfile name (default commented)
    # This is the *Apache compatible* log file, not the twisted-style logfile.
    # Leaving this as None will have no Apache compatible log file. Apache
    # compatible logfiles are useful because there are quite a few programs
    # which analyze them and display statistics.
    ## logPath_twisted = 'mointwisted.log'

    # moin log file
    ## logPath = 'moin.log'

    # Memory profile (default commented)
    # Useful only if you are a developer or interested in moin memory usage
    ## from MoinMoin.util.profile import TwistedProfiler
    ## memoryProfile = TwistedProfiler('mointwisted',
    ##                            requestsPerSample=100,
    ##                            collect=0)

    # Hotshot profile (default commented)
    # Not compatible with threads.
    ## hotshotProfile = name + '.prof'


# Create the application
application = makeApp(Config)

