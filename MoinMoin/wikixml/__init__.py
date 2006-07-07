# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Package Initialization

    Subpackage containing XML support code.

    @copyright: 2001, 2002 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

try:
    from xml.sax import saxutils
    ok = hasattr(saxutils, 'quoteattr') # check for correct patch level
except ImportError:
    ok = 0

