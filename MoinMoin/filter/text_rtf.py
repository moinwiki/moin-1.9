# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RichTextFormat filter

    Depends on: catdoc command from catdoc package
    
    @copyright: 2006 by ThomasWaldmann MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import filter

def execute(indexobj, filename):
    return filter.execfilter("catdoc %s", filename)

