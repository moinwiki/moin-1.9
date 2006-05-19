# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Extension Script Package

    @copyright: 2006 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

# create a list of extension scripts from the subpackage directory
extension_scripts = pysupport.getPackageModules(__file__)
modules = extension_scripts

