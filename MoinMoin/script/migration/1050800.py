#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - 1st pass of 1.6 migration

    @copyright: 2007 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from _conv160 import DataConverter

def execute(script, data_dir, rev):
    # the first pass just creates <data_dir>/rename1.txt
    dc = DataConverter(data_dir, None)
    dc.pass1()
    return 1059999


if __name__ == '__main__':
    execute(None, './data', None)

