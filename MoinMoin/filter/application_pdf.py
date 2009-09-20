# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PDF filter

    Depends on: pdftotext command from either xpdf-utils or poppler-utils
                or any other package that provides a pdftotext command that
                is callable with: pdftotext -enc UTF-8 filename.pdf -

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.filter import execfilter

def execute(indexobj, filename):
    return execfilter("pdftotext -enc UTF-8 %s -", filename)

