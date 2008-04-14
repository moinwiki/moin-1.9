# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - init "logging" system

    WARNING
    -------
    logging must be configured VERY early, before any moin module calls
    log.getLogger(). Because most modules call getLogger on the module
    level, this basically means that MoinMoin.log must be imported first
    and load_config must be called afterwards, before any other moin
    module gets imported.

    Usage (for wiki server admins)
    ------------------------------
    Typically, your server adaptor script (e.g. moin.cgi) will have this:

    from MoinMoin import log
    log.load_config('wiki/config/logging/logfile') # XXX please fix this path!

    You have to fix that path to use a logging configuration matching your
    needs (we provide some examples in the path given there, it is relative to
    the uncompressed moin distribution archive - if you use some moin package,
    you maybe find it under /usr/share/moin/).
    It is likely that you also have to edit the sample logging configurations
    we provide (e.g. to fix the logfile location).

    Usage (for developers)
    ----------------------
    If you write code for moin, do this at top of your module:

    from MoinMoin import log
    logging = log.getLogger(__name__)

    This will create a logger with 'MoinMoin.your.module' as name.
    The logger can optionally get configured in the logging configuration.
    If you don't configure it, some upperlevel logger (e.g. the root logger)
    will do the logging.

    @copyright: 2008 MoinMoin:ThomasWaldmann,
                2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

# This is the "last resort" fallback logging configuration for the case
# that load_config() is either not called at all or with a non-working
# logging configuration.
# See http://www.python.org/doc/lib/logging-config-fileformat.html
# We just use stderr output by default, if you want anything else,
# you will have to configure logging.
logging_defaults = {
    'loglevel': 'INFO',
}
logging_config = """\
[loggers]
keys=root

[handlers]
keys=stderr

[formatters]
keys=default

[logger_root]
level=%(loglevel)s
handlers=stderr

[handler_stderr]
class=StreamHandler
level=NOTSET
formatter=default
args=(sys.stderr, )

[formatter_default]
format=%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s
datefmt=
class=logging.Formatter
"""

import logging, logging.config

configured = False
fallback_config = False


def load_config(conf_fname):
    """ load logging config from conffile """
    global configured
    try:
        logging.config.fileConfig(conf_fname)
        configured = True
    except Exception, err: # XXX be more precise
        load_fallback_config(err)

def load_fallback_config(err=None):
    """ load builtin fallback logging config """
    global configured
    from StringIO import StringIO
    logging.config.fileConfig(StringIO(logging_config), logging_defaults)
    configured = True
    l = getLogger(__name__)
    l.warning('Using built-in fallback logging configuration!')
    if err:
        l.warning('load_config failed with "%s".' % str(err))


def getLogger(name):
    """ wrapper around logging.getLogger, so we can do some more stuff:
        - preprocess logger name
        - patch loglevel constants into logger object, so it can be used
          instead of the logging module
    """
    if not configured: # should not happen
        load_fallback_config()
    logger = logging.getLogger(name)
    for levelnumber, levelname in logging._levelNames.items():
        if isinstance(levelnumber, int): # that list has also the reverse mapping...
            setattr(logger, levelname, levelnumber)
    return logger


# Python 2.3's logging module has no .log, this provides it:
if not hasattr(logging, 'log'):
    def log(level, msg, *args, **kwargs):
        if len(logging.root.handlers) == 0:
            logging.basicConfig()
        if logging.root.manager.disable >= level:
            return
        if level >= logging.root.getEffectiveLevel():
            logging.root._log(level, msg, args, **kwargs)
    logging.log = log

