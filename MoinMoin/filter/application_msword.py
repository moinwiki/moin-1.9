# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - msword filter

    Depends on: antiword command from antiword package

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.filter import execfilter

def execute(indexobj, filename):
    return execfilter("HOME=/tmp antiword '%s'", filename) # no HOME makes antiword complain

