# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - text/xml file Filter

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.filter.text_xml import execute as xmlfilter

def execute(indexobj, filename):
    return xmlfilter(indexobj, filename)

