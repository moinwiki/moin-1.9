"""
    MoinMoin - WSGI application

    @copyright: 2005 by Anakim Border <akborder@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

use_threads = True
unixSocketPath = '/tmp/moin.sock'

# Set threads flag, so other code can use proper locking
from MoinMoin import config
config.use_threads = use_threads
del config

from flup.server.fcgi import WSGIServer
from MoinMoin.server.wsgi import moinmoinApp
import os

if __name__ == '__main__':
    server = WSGIServer(moinmoinApp, bindAddress=unixSocketPath)
    server.run()
    os.unlink(unixSocketPath)

