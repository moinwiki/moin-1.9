# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - OpenOffice.org 2.x Writer Filter (OpenDocument Text)

    Depends on: nothing (only python with zlib)

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.filter.application_vnd_oasis_opendocument import execute as odfilter

def execute(indexobj, filename):
    return odfilter(indexobj, filename)

