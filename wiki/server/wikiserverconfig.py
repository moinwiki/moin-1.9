"""
    Standalone server configuration, you can either use this file or
    commandline options to configure server options.
"""
import os

from MoinMoin.script.server.standalone import DefaultConfig


class LocalConfig(DefaultConfig):
    # where the static data is served from - you can either use:
    # docs = True  # serve the builtin static data from MoinMoin/web/static/htdocs/
    # docs = '/where/ever/you/like/to/keep/htdocs'  # serve it from the given path
    # docs = False  # do not serve static files at all (will not work except
    #               # you serve them in some other working way)
    #docs = True

    # if you start the server as root, the standalone server can change
    # to this user and group, e.g. 'www-data'
    #user = None
    #group = None

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
    #debug = os.environ.get('MOIN_DEBUGGER', 'off')

    # should the exception evaluation feature be enabled?
    #use_evalex = True

    # Werkzeug run_simple arguments below here:

    # use '' for all interfaces or "1.2.3.4" for some specific IP
    hostname = 'localhost'
    # if you use port < 1024, you need to start as root
    port = 8080

    # either multi-thread or multi-process (not both):
    # threaded = True, processes = 1 is usually what you want
    # threaded = False, processes = 10 (for example) can be rather slow
    # thus, if you need a forking server, maybe rather use apache/mod-wsgi!
    #threaded = True
    #processes = 1

    # automatic code reloader - needs testing!
    #use_reloader = False
    #extra_files = None
    #reloader_interval = 1

    # we can't use static_files to replace our own middleware setup for moin's
    # static files, because we also need the setup with other servers (like
    # apache), not just when using werkzeug's run_simple server.
    # But you can use it if you need to serve other static files you just need
    # with the standalone wikiserver.
    #static_files = None


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
