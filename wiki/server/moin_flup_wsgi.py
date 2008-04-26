"""
    MoinMoin - Moin as WSGI application with flup as fcgi gateway

    @copyright: 2005 by Anakim Border <akborder@gmail.com>,
                2008 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

use_threads = True
unixSocketPath = '/tmp/moin.sock'

import os

from MoinMoin import log
log.load_config('wiki/config/logging/logfile') # XXX please fix this path!

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

