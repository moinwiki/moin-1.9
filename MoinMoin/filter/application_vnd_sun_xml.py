# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - OpenOffice.org *.sx? Filter

    Depends on: nothing (only python with zlib)

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import re, zipfile

rx_stripxml = re.compile("<[^>]*?>", re.DOTALL|re.MULTILINE)

def execute(indexobj, filename):
    try:
        zf = zipfile.ZipFile(filename, "r")
        data = zf.read("content.xml")
        zf.close()
        data = " ".join(rx_stripxml.sub(" ", data).split())
    except RuntimeError, err:
        indexobj.request.log(str(err))
        data = ""
    return data.decode('utf-8')

