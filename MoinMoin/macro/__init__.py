# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Macro Package

    The canonical interface to macros is their execute() function,
    which gets passed an instance of the Macro class. Such an instance
    has the four members parser, formatter, form and request.

    Using "form" directly is deprecated and should be replaced
    by "request.form".

    Besides the execute() function, macros can export additional
    functions to offer services to other macros or actions. A few
    actually do that, e.g. AttachFile.

    @copyright: 2000 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

extension_macros = pysupport.getPackageModules(__file__)
modules = extension_macros
