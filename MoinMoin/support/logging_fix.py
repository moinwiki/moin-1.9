# -*- coding: iso-8859-1 -*-
"""
    Python 2.3's logging module has no .log, this provides it.

    @copyright: 2007 MoinMoin:JohannesBerg 
    @license: GNU GPL, see COPYING for details.
"""

import logging
if not hasattr(logging, 'log'):
    def log(level, msg, *args, **kwargs):
        if len(logging.root.handlers) == 0:
            logging.basicConfig()
        if logging.root.manager.disable >= level:
            return
        if level >= logging.root.getEffectiveLevel():
            logging.root._log(level, msg, args, **kwargs)
    logging.log = log
