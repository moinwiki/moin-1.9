# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Extension Action Package

    @copyright: 2000 by Richard Jones <richard@bizarsoftware.com.au>
    @copyright: 2000, 2001, 2002 by Jürgen Hermann <jh@web.de>  
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

# create a list of extension actions from the subpackage directory
extension_actions = pysupport.getPackageModules(__file__)
modules = extension_actions
