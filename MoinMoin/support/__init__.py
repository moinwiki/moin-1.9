# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Support Package

    This package collects small third party utilities in order
    to reduce the necessary steps in installing MoinMoin. Each
    source file is copyrighted by its respective author. We've done
    our best to assure those files are freely redistributable.

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

try:
    sorted = sorted
except NameError:
    def sorted(l, *args, **kw):
        l = l[:]
        # py2.3 is a bit different
        if 'cmp' in kw:
            args = (kw['cmp'], )

        l.sort(*args)
        return l

