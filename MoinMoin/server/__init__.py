# -*- coding: iso-8859-1 -*-
"""
    MoinMoin server package

    Supply common server utilities.

    @copyright: 2004 Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

import os
from StringIO import StringIO

from MoinMoin import config

import logging as _logging

def configureLogging(conf, defaults):
   from logging.config import fileConfig
   fileConfig(StringIO(conf), defaults)

def getLogger(name):
    # do we want to strip MoinMoin. from the name?
    #if name.startswith('MoinMoin.'):
    #    name = name[9:]
    logger = _logging.getLogger(name)
    for levelnumber, levelname in _logging._levelNames.items():
        if isinstance(levelnumber, int): # that list has also the reverse mapping...
            setattr(logger, levelname, levelnumber)
    return logger

logging = getLogger(__name__)

# use this to temporarily and selectively enable debug logging for this module
#logging.setLevel(logging.DEBUG)

def switchUID(uid, gid):
    """ Switch identity to safe user and group

    Does not support Windows, because the necessary calls are not available.
    TODO: can we use win32api calls to achieve the same effect on Windows?

    Raise RuntimeError if can't switch or trying to switch to root.
    """
    if uid == 0 or gid == 0:
        # We will not run as root. If you like to run a web
        # server as root, then hack this code.
        raise RuntimeError('will not run as root!')

    try:
        os.setgid(gid)
        os.setuid(uid)
    except (OSError, AttributeError):
        # Either we can't switch, or we are on windows, which does not have
        # those calls.
        raise RuntimeError("can't change uid/gid to %s/%s" %
                           (uid, gid))
    logging.info("Running as uid/gid %d/%d" % (uid, gid))


class Config:
    """ Base class for server configuration

    When you create a server, you should run it with a Config
    instance. Sub class to define the default values.

    This class does all error checking needed for config values, and will
    raise a RuntimeError on any fatal error.
    """
    # some defaults that should be common for all servers:
    url_prefix_static = config.url_prefix_static
    docs = None # document root (if supported)
    user = None # user we shall use for running (if supported)
    group = None # group ...
    port = None # tcp port number (if supported)

    # Here you can configure the default logging used when running moin,
    # see http://www.python.org/doc/lib/logging-config-fileformat.html
    # We just use moin.log in current directory by default, if you want
    # anything else, override logging_conf in your server script's Config class.
    logging_defaults = {
        'logdir': '.',
        'loglevel': 'DEBUG',
}
    logging_config = """\
[loggers]
keys=root

[handlers]
keys=logfile

[formatters]
keys=logfile

[logger_root]
level=%(loglevel)s
handlers=logfile

[handler_logfile]
class=StreamHandler
level=NOTSET
formatter=logfile
args=('%(logdir)s/moin.log', 'at')

[formatter_logfile]
format=%(asctime)s %(name)s %(levelname)s %(message)s
datefmt=
class=logging.Formatter
"""

    def __init__(self):
        """ Validate and post process configuration values

        Will raise RuntimeError for any wrong config value.
        """
        # First, initialize the logging
        configureLogging(self.logging_config, self.logging_defaults)

        # Check that docs path is accessible
        if self.docs:
            self.docs = os.path.normpath(os.path.abspath(self.docs))
            if not os.access(self.docs, os.F_OK | os.R_OK | os.X_OK):
                raise RuntimeError("Can't access docs directory '%s'. Check docs "
                                   "setting and permissions." % self.docs)

        # Don't check uid and gid on windows, those calls are not available.
        if os.name == 'nt':
            self.uid = self.gid = 0
            return

        self.uid = os.getuid()
        self.gid = os.getgid()

        # If serving privileged port, we must run as root to bind the port.
        # we will give up root privileges later
        if self.port and self.port < 1024 and self.uid != 0:
            raise RuntimeError('Must run as root to serve port number under 1024. '
                               'Run as root or change port setting.')

        if self.user and self.group and self.uid == 0:
            # If we run as root to serve privileged port, we change user and group
            # to a safe setting. Get the uid and gid now, switch later.
            import pwd, grp
            try:
                self.uid = pwd.getpwnam(self.user)[2]
            except KeyError:
                raise RuntimeError("Unknown user: '%s', check user setting" % self.user)
            try:
                self.gid = grp.getgrnam(self.group)[2]
            except KeyError:
                raise RuntimeError("Unknown group: '%s', check group setting" % self.group)

