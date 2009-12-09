# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Import Script Package

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

# create a list of extension scripts from the subpackage directory
import_scripts = pysupport.getPackageModules(__file__)
modules = import_scripts

