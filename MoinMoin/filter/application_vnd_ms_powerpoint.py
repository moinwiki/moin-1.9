# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - mspowerpoint filter

    Depends on: "catppt" command from "catdoc" package

    @copyright: 2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.filter import execfilter

def execute(indexobj, filename):
    data = execfilter("catppt -dutf-8 %s", filename)
    return data

