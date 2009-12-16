#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - 2nd pass of 1.6 migration

    @copyright: 2007 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, shutil

from _conv160a import DataConverter

def execute(script, data_dir, rev):
    rename1_map = os.path.join(data_dir, 'rename1.txt')
    rename2_map = os.path.join(data_dir, 'rename2.txt')
    fieldsep = DataConverter.LIST_FIELDSEP
    if fieldsep == u'\t':
        fieldsep = u'TAB'
    if not os.path.exists(rename2_map):
        print "You must first edit %s." % rename1_map
        print "For editing it, please use an editor that is able to edit UTF-8 encoded files."
        print "Carefully edit - the fields are separated by a %s char, do not change this!" % fieldsep
        print "Entries in this file look like:"
        print "PAGE OLDPAGENAME NEWPAGENAME"
        print "FILE OLDPAGENAME OLDFILENAME NEWFILENAME"
        print "You may ONLY edit the rightmost field (the new name - in case you want to rename the page or file)."
        print
        print "After you have finished editing, rename the file to %s and re-issue the moin migrate command." % rename2_map
        return None # terminate here
    # the second pass does the conversion, reading <data_dir>/rename2.txt
    src_data_dir = os.path.abspath(os.path.join(data_dir, '..', 'data.pre160')) # keep the orig data_dir here
    dst_data_dir = data_dir
    shutil.move(data_dir, src_data_dir)
    # the 1.5 parser checks page existance, so we must use the orig, fully populated dir:
    saved_data_dir = script.request.cfg.data_dir
    script.request.cfg.data_dir = src_data_dir
    os.mkdir(dst_data_dir)
    shutil.move(os.path.join(src_data_dir, 'cache'), os.path.join(dst_data_dir, 'cache')) # mig script has locks there
    dc = DataConverter(script.request, src_data_dir, dst_data_dir)
    dc.pass2()
    # restore correct data dir:
    script.request.cfg.data_dir = saved_data_dir
    return 1060000

