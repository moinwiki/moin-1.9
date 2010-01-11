# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - migration from base rev 1050300

    We add a filter plugin dir here.

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.script.migration.migutil import opj, listdir, copy_file, move_file, copy_dir, makedir

def execute(script, data_dir, rev):
    plugindir = opj(data_dir, 'plugin')
    for d in ['filter', ]:
        thisdir = opj(plugindir, d)
        makedir(thisdir)
        fname = opj(thisdir, '__init__.py')
        f = open(fname, 'w')
        f.write("""\
# -*- coding: iso-8859-1 -*-

from MoinMoin.util import pysupport

modules = pysupport.getPackageModules(__file__)
""")
        f.close()
    return rev + 1

