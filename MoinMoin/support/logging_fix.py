# -*- coding: utf-8 -*-
"""
Python 2.3's logging module has no .log, this provides it.
"""

import logging
if not hasattr(logging, 'log'):
    def log(level, msg, *args, **kwargs):
        if len(logging.root.handlers) == 0:
            logging.basicConfig()
        if logging.root.manager.disable >= level:
            return
        if level >= logging.root.getEffectiveLevel():
            apply(logging.root._log, (level, msg, args), kwargs)
    logging.log = log
