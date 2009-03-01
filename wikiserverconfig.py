"""
    Standalone server configuration, you can either use this file or
    commandline options to configure server options.
"""
import os

from MoinMoin.script.server.standalone import DefaultConfig

class Config(DefaultConfig):
    port = 8080 # if you use port < 1024, you need to start as root

    # if you start the server as root, the standalone server can change
    # to this user and group, e.g. 'www-data'
    #user = ''
    #group = ''

    # use '' for all interface or "1.2.3.4" for some specific IP
    #interface = 'localhost'

    # where the static data is served from - you can either use:
    # docs = True  # serve the builtin static data from MoinMoin/web/static/htdocs
    # docs = '/where/ever/you/like/to/keep/htdocs'  # serve it from the given path
    # docs = False  # do not serve static files at all (will not work except
    #               # you serve them in some other working way)
    docs = True

    # tuning options:
    #serverClass = 'ThreadPoolServer'
    #threadLimit = 10
    #requestQueueSize = 50

    # Use werkzeug's debugging middleware?
    # debug can be either set to True or False to directly enable/disable
    # the debugger.
    # CAUTION: Do not use True for production environments as it might disclose
    # sensitive informations and even enable doing evil things from the
    # debugger's web interface!
    # For convenience, the default behaviour (see below) is to read the
    # environment variable MOIN_DEBUGGER. Setting it to True will enable the
    # debugger, anything else (or not setting it) will disable the debugger.
    debug = os.environ.get('MOIN_DEBUGGER', 'False') == 'True'

