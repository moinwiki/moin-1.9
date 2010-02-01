"""
    Standalone server configuration, you can either use this file or
    commandline options to configure server options.
"""

from MoinMoin.script.server.standalone import DefaultConfig

class Config(DefaultConfig):
    port = 8080 # if you use port < 1024, you need to start as root

    # if you start the server as root, the standalone server can change
    # to this user and group, e.g. 'www-data'
    #user = ''
    #group = ''

    # use '' for all interface or "1.2.3.4" for some specific IP
    #interface = 'localhost'

    # where the static data is served from:
    #docs = "/usr/share/moin/htdocs"

    # tuning options:
    #serverClass = 'ThreadPoolServer'
    #threadLimit = 10
    #requestQueueSize = 50

