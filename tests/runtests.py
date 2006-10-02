# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Run Unit tests

Usage:

    runtests [test_name...]

Without arguments run all the tests in the _tests package.

@copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
@license: GNU GPL, see COPYING for details.
"""

import os, sys

from MoinMoin import _tests

def run():
    _tests.run(names=sys.argv[1:])


if __name__ == '__main__':
    run()

