# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Processor Package

    DEPRECATED!

    Please use Parsers instead of Processors.

    @copyright: 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport

processors = pysupport.getPackageModules(__file__)
modules = processors
