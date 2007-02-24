# -*- coding: iso-8859-1 -*-
"""
    MoinMoin server package

    Supply common server utilities.

    @copyright: 2004 by Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

import os
import logging

from MoinMoin import config

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

    # log levels for different log handlers
    # None means "don't use this handler", otherwise specify the minimum loglevel, e.g. logging.DEBUG
    # TODO: change later to an appropriate level, for now, we want everything
    loglevel_file = logging.DEBUG # None
    loglevel_stderr = logging.DEBUG # None
    logPath = None

    def __init__(self):
        """ Validate and post process configuration values

        Will raise RuntimeError for any wrong config value.
        """
        # First, initialize the logging
        logger = logging.getLogger('') # root logger
        logger.setLevel(logging.NOTSET) # otherwise it has WARNING by default!

        if self.loglevel_file is not None and self.logPath is not None:
            # define a Handler which writes to a log file
            logfile = logging.FileHandler(self.logPath, 'at') # XXX we can't say ", 0" for sync here :(
            logfile.setLevel(self.loglevel_file)
            # set a format which is better for logfile use
            formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
            # tell the handler to use this format
            logfile.setFormatter(formatter)
            # add the handler to the root logger
            logger.addHandler(logfile)

        if self.loglevel_stderr is not None:
            # define a Handler which writes INFO to sys.stderr
            logstderr = logging.StreamHandler()
            logstderr.setLevel(self.loglevel_stderr)
            # set a format which is simpler for console use
            formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', '%H%M%S')
            # tell the handler to use this format
            logstderr.setFormatter(formatter)
            # add the handler to the root logger
            logger.addHandler(logstderr)

        logging.info("logging initialized")

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

