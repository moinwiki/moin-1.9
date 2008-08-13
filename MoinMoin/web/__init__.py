# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This package contains the interface between webserver
               and application. This is meant to become a replacement
               and/or port of code currently scattered in MoinMoin.request
               and MoinMoin.server.

    @copyright: 2008-2008 MoinMoin:FlorianKrupicka
    @license: GNU GPL, see COPYING for details.
"""

def _fixup_deps():
    """
    Alter the system path to import some 3rd party dependencies from
    inside the MoinMoin.support package. This is meant for deps
    used inside this package, which are mainly werkzeug and flup.
    """
    import sys, os
    from MoinMoin import support
    dirname = os.path.dirname(support.__file__)
    dirname = os.path.abspath(dirname)
    found = False
    for path in sys.path:
        if os.path.abspath(path) == dirname:
            found = True
            break
    if not found:
        sys.path.append(dirname)

try:
    _fixup_deps()
finally:
    del _fixup_deps
