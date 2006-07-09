# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Extension Converter Package

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

# create a list of extension converters from the subpackage directory
extension_converters = pysupport.getPackageModules(__file__)
modules = extension_converters
