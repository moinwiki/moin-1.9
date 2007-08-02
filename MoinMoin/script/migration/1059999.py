#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - 2nd pass of 1.6 migration

    @copyright: 2007 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, shutil

from _conv160 import DataConverter

def execute(script, data_dir, rev):
    rename1_map = os.path.join(data_dir, 'rename1.txt')
    rename2_map = os.path.join(data_dir, 'rename2.txt')
    if not os.path.exists(rename2_map):
        print "You must first edit %s." % rename1_map
        print "For editing it, please use an editor that honours TAB chars and is able to edit UTF-8 encoded files."
        print "Carefully edit - the fields are separated by a single TAB char, do not change this!"
        print "You may ONLY edit the rightmost field (this is the NEW name - in case you want to rename the page or file)."
        print
        print "After you have finished editing, rename the file to %s and re-issue the moin migrate command." % rename2_map
        return None # terminate here
    # the second pass does the conversion, reading <data_dir>/rename2.txt
    src_data_dir = os.path.abspath(os.path.join(data_dir, '..', 'data.pre160')) # keep the orig data_dir here
    dst_data_dir = data_dir
    shutil.move(data_dir, src_data_dir)
    dc = DataConverter(None, src_data_dir, dst_data_dir) # XXX TODO None -> script.request
    dc.pass2()
    return 1060000


if __name__ == '__main__':
    execute(None, './data', None)

