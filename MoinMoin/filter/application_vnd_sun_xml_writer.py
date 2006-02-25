# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - OpenOffice SXW Filter

    @copyright: 2006 by ThomasWaldmann MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import re, sys
import zipfile

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

