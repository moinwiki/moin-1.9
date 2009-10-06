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
    # using -q switch to get quiet operation (no messages, no errors),
    # because poppler-utils pdftotext on Debian/Etch otherwise generates
    # lots of output on stderr (e.g. 10MB stderr output) and that causes
    # problems in current execfilter implementation.
    return execfilter("pdftotext -q -enc UTF-8 %s -", filename)

