"""
    Standalone server configuration, you can either use this file or
    commandline options to configure server options.
"""
import os

from MoinMoin.script.server.standalone import DefaultConfig

class LocalConfig(DefaultConfig):
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

    # How to debug? Your options:
    # debug = 'off' # for production wikis, exceptions are logged
    # debug = 'web' # show traceback in the browser, offer debug console,
    #               # this makes use of a built-in debugger (werkzeug.debug)
    # debug = 'external' # don't catch Exceptions, so some external debugger gets them
    # CAUTION: Do not use anything but 'off' for production environments as it
    #          might disclose sensitive informations and even enable doing evil
    #          things from some debugger's web interface!
    # For convenience, the default behaviour (see below) is to read the
    # environment variable MOIN_DEBUGGER. If not set, it means the same as 'off'.
    debug = os.environ.get('MOIN_DEBUGGER', 'off')

# DEVELOPERS! Do not add your configuration items there,
# you could accidentally commit them! Instead, create a
# wikiserverconfig_local.py file containing this:
#
# from wikiserverconfig import LocalConfig
#
# class Config(LocalConfig):
#     configuration_item_1 = 'value1'
#

try:
    from wikiserverconfig_local import Config
except ImportError, err:
    if not str(err).endswith('wikiserverconfig_local'):
        raise
    Config = LocalConfig
