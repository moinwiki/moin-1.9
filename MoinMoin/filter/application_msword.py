# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - msword filter

    Depends on: antiword command from antiword package

    @copyright: 2006-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os

from MoinMoin.filter import execfilter

def execute(indexobj, filename):
    cmd = "antiword %s"
    if os.name == 'posix':
        cmd = "HOME=/tmp " + cmd  # no HOME makes antiword complain (on Linux)
    return execfilter(cmd, filename)

