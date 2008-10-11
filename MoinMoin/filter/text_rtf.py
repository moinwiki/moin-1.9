# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RichTextFormat filter

    Depends on: catdoc command from catdoc package

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.filter import execfilter

def execute(indexobj, filename):
    return execfilter("catdoc %s", filename)

