# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - msword filter

    Depends on: antiword command from antiword package
    
    @copyright: 2006 by ThomasWaldmann MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import filter

def execute(indexobj, filename):
    return filter.execfilter("HOME=/tmp antiword '%s'", filename) # no HOME makes antiword complain

