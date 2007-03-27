# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - text/* file Filter

    We try to support more than ASCII here.

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import codecs

def execute(indexobj, filename):
    for enc in ('utf-8', 'iso-8859-15', ):
        try:
            f = codecs.open(filename, "r", enc)
            data = f.read()
            f.close()
            return data
        except UnicodeError:
            pass
    f = file(filename, "r")
    data = f.read()
    f.close()
    data = data.decode('ascii', 'replace')
    return data

