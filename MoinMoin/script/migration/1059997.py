#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - 1st pass of 1.6a to 1.6 migration

    Note: this is a special hack for some users of a early 1.6 alpha version,
          this code is skipped and NOT executed in a normal release-to-release
          migration (like when going from 1.5.x release to 1.6.0 release).

          If you run this early 1.6alpha code (with different link markup than
          1.5.x AND 1.6.x release has), you need to manually put 1059997 into
          your data/meta file to have this special code executed.

    @copyright: 2008 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from _conv160a import DataConverter

def execute(script, data_dir, rev):
    # the first pass just creates <data_dir>/rename1.txt
    dc = DataConverter(script.request, data_dir, None)
    dc.pass1()
    return 1059998

