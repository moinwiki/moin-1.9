# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Server Script Package

    @copyright: 2008 MoinMoin:ForrestVoight
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

# create a list of extension scripts from the subpackage directory
server_scripts = pysupport.getPackageModules(__file__)
modules = server_scripts

