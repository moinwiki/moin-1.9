# -*- coding: iso-8859-1 -*-
"""
MoinMoin - reducewiki script

@copyright: 2005-2006 MoinMoin:ThomasWaldmann
@license: GPL, see COPYING for details
"""

import os, shutil, codecs

from MoinMoin import config, wikiutil
from MoinMoin.Page import Page
from MoinMoin.action import AttachFile

from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to reduce a data/ directory to just the latest page
revision of each non-deleted page (plus all attachments).

This is used to make the distributed underlay directory, but can also be
used for other purposes.

So we change like this:
    * data/pages/PageName/revisions/{1,2,3,4}
        -> data/pages/revisions/1  (with content of 4)
    * data/pages/PageName/current (pointing to e.g. 4)
        -> same (pointing to 1)
    * data/pages/PageName/edit-log and data/edit-log
        -> do not copy
    * data/pages/PageName/attachments/*
        -> just copy

Detailed Instructions:
======================
General syntax: moin [options] maint reducewiki [reducewiki-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[reducewiki-options] see below:
    0. To create a wiki data/ directory with just the latest revisions in the
       directory '/mywiki'
       moin ... maint reducewiki --target-dir=/mywiki
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "-t", "--target-dir", dest="target_dir",
            help="Write reduced wiki data to DIRECTORY."
        )

    def copypage(self, request, rootdir, pagename):
        """ quick and dirty! """
        pagedir = os.path.join(rootdir, 'pages', wikiutil.quoteWikinameFS(pagename))
        os.makedirs(pagedir)

        # write a "current" file with content "00000001"
        revstr = '%08d' % 1
        cf = os.path.join(pagedir, 'current')
        file(cf, 'w').write(revstr+'\n')

        # create a single revision 00000001
        revdir = os.path.join(pagedir, 'revisions')
        os.makedirs(revdir)
        tf = os.path.join(revdir, revstr)
        p = Page(request, pagename)
        text = p.get_raw_body().replace("\n", "\r\n")
        codecs.open(tf, 'wb', config.charset).write(text)

        source_dir = AttachFile.getAttachDir(request, pagename)
        if os.path.exists(source_dir):
            dest_dir = os.path.join(pagedir, "attachments")
            os.makedirs(dest_dir)
            for filename in os.listdir(source_dir):
                source_file = os.path.join(source_dir, filename)
                dest_file = os.path.join(dest_dir, filename)
                shutil.copyfile(source_file, dest_file)

    def mainloop(self):
        self.init_request()
        request = self.request
        request.form = request.args = request.setup_args()
        destdir = self.options.target_dir
        pagelist = list(request.rootpage.getPageList(user=''))
        for pagename in pagelist:
            self.copypage(request, destdir, pagename)

