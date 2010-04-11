# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - data_dir migration main script (new style)

    You can use this script to migrate your wiki's data_dir to the format
    expected by the current MoinMoin code. It will read data/meta to determine
    what needs to be done and call other migration scripts as needed.

    You must run this script as owner of the wiki files, usually this is the
    web server user (like www-data).

    Important: you must have run all 12_to_13* and the final 152_to_1050300
               mig scripts ONCE and in correct order manually before attempting
               to use the new style migration stuff.

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os

from MoinMoin import wikiutil
from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allow you to migrate data of pages to a newer version

Detailed Instructions:
======================
General syntax: moin [options] migration data [migration-data-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[migration-data-options] see below:
    Please note:
    * You must run this script as the owner of the wiki files.
    * The file docs/UPDATE.html contains the general instructions
      for upgrading a wiki.
"""


    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "--all", action="store_true", dest="all_wikis",
            help="when given, update all wikis that belong to this farm"
        )

    def mainloop(self):
        self.init_request()
        request = self.request
        data_dir = request.cfg.data_dir
        meta_fname = os.path.join(data_dir, 'meta')
        while True:
            try:
                meta = wikiutil.MetaDict(meta_fname, request.cfg.cache_dir)
                try:
                    curr_rev = meta['data_format_revision']
                    mig_name = str(curr_rev)
                    execute = wikiutil.importBuiltinPlugin('script.migration', mig_name)
                    print "Calling migration script for %s, base revision %d" % (data_dir, curr_rev)
                    curr_rev = execute(self, data_dir, curr_rev)
                    if curr_rev is None:
                        print "Final mig script reached, migration is complete."
                        break
                    else:
                        print "Returned. New rev is %d." % curr_rev
                        meta['data_format_revision'] = curr_rev
                        meta.sync()
                except wikiutil.PluginMissingError:
                    print "Error: There is no script for %s." % mig_name
                    break
            finally:
                del meta

