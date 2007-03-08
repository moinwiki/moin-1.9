#!/usr/bin/env python
"""
    Start script for the standalone Wiki server.

    @copyright: 2004-2006 Thomas Waldmann, Nir Soffer, Alexander Schremmer
    @license: GNU GPL, see COPYING for details.
"""

print "Loading ..."

import os, sys

class PythonTooOldError:
    pass

try:
    if sys.version_info[:3] < (2, 3, 0):
        raise PythonTooOldError
except:
    sys.exit("Unfortunately, your installed Python is too old. Please download at "
             "least Python 2.3.0 (Python 2.4.3 is recommended).\n\n"
             "You can get Python here: http://www.python.org/download/")


# We insert the path where THIS script is located into the python search path.
# If your wikiconfig.py / farmconfig.py / etc. is located there, this is all
# you'll need.
moinpath = os.path.abspath(os.path.normpath(os.path.dirname(sys.argv[0])))
sys.path.insert(0, moinpath)

# Path of the directory where wikiconfig.py is located.
# YOU MAYBE NEED TO CHANGE THIS TO MATCH YOUR SETUP.
#sys.path.insert(0, '/path/to/wikiconfig')

# Path to MoinMoin package, needed if you installed with --prefix=PREFIX
# or if you did not use setup.py.
#sys.path.insert(0, 'PREFIX/lib/python2.3/site-packages')

# Path of the directory where farmconfig is located (if different).
#sys.path.insert(0, '/path/to/farmconfig')

# Debug mode - show detailed error reports
## import os
## os.environ['MOIN_DEBUG'] = '1'

from MoinMoin.server.STANDALONE import StandaloneConfig, run
from MoinMoin.version import project, release, revision

print "%s - %s [%s]" % (project, release, revision)

if os.name == 'nt':
    print
    print "Just close this window to shutdown MoinMoin DesktopEdition."
print


class DefaultConfig(StandaloneConfig):

    # Server name
    # Used to create .log, .pid and .prof files
    name = 'moin'

    # Path to moin shared files (default '/usr/share/moin/wiki/htdocs')
    # If you installed with --prefix=PREFIX, use 'PREFIX/share/moin/wiki/htdocs'
    #docs = '/usr/share/moin/htdocs'
    # If your wiki/ directory is below the moin.py command, you don't need to
    # change this:
    docs = os.path.join(moinpath, 'wiki', 'htdocs')

    # URL prefix for the static stuff (used to access stuff in docs) - you
    # usually should not need to change this because moin standalone uses
    # matching defaults for here and for wikiconfig.py:
    #url_prefix_static = '/moin_static160'

    # The server will run with as this user and group (default 'www-data')
    #user = 'www-data'
    #group = 'www-data'

    # Port (default 8000)
    # To serve privileged port under 1024 you will have to run as root
    port = 8080

    # Interface (default 'localhost')
    # '' - will listen to any interface
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
    #serverClass = 'ThreadPoolServer'

    # Thread limit (default 10)
    # Limit the number of threads created. Ignored on non threaded servers.
    #threadLimit = 10

    # Request queue size (default 50)
    # The size of the socket listen backlog.
    #requestQueueSize = 50

    # Properties
    # Allow overriding any request property by the value defined in
    # this dict e.g properties = {'script_name': '/mywiki'}.
    #properties = {}

    # Memory profile (default commented)
    # Useful only if you are a developer or interested in moin memory usage
    # A memory profile named 'moin--2004-09-27--01-24.log' is
    # created each time you start the server.
    ## from MoinMoin.util.profile import Profiler
    ## memoryProfile = Profiler(name, requestsPerSample=100, collect=0)

    # Hotshot profile (default commented)
    # Not compatible with threads - use with SimpleServer only.
    ## hotshotProfile = name + '.prof'


try:
    from wikiserverconfig import Config
except ImportError:
    Config = DefaultConfig

if __name__ == '__main__':
    # Run moin moin server:
    run(Config)

