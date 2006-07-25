# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Filter Package

    @copyright: 2006 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os
from MoinMoin.util import pysupport

filters = pysupport.getPackageModules(__file__)
modules = filters

standard_codings = ['utf-8', 'iso-8859-15', 'iso-8859-1', ]

def execfilter(cmd, filename, codings=standard_codings):
    """ use cmd to get plaintext content of filename
        to decode to unicode, we use the first coding of codings list that
        does not throw an exception or force ascii
    """
    f = os.popen(cmd % filename)
    data = f.read()
    f.close()
    for c in codings:
        try:
            return data.decode(c)
        except UnicodeError:
            pass
    return data.decode('ascii', 'replace')

