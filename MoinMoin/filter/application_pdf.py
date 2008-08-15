# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PDF filter

    Depends on: pdftotext command from xpdf-utils package

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.filter import execfilter

def execute(indexobj, filename):
    return execfilter("pdftotext -enc UTF-8 %s -", filename)

