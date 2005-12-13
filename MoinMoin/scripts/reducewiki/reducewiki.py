#!/usr/bin/env python
"""
    Use this script to reduce a data/ directory to the latest page revision of
    each non-deleted page (plus all attachments).
    
    This is used to make the distributed underlay directory, but can also be
    used for other purposes.
    
    So we change like this:      
        * data/pages/PageName/revisions/{1,2,3,4}
          -> data/pages/revisions/1
        * data/pages/PageName/current (pointing to e.g. 4)
          -> same (pointing to 1)
        * data/pages/PageName/edit-log and data/edit-log
          -> do not copy
        * data/pages/PageName/attachments/*
          -> just copy

    Steps for a successful conversion:

        1. Stop your wiki and make a backup of old data and code

        2. Make a copy of the wiki's "data" directory to your working dir

        3. Run this script from your working dir

        4. If there was no error, you will find:
            data.pre-reduce - the script renames your data directory copy to that name
            data - reduced data dir

        5. Verify conversion results (number of pages, ...)

        6. Test it - if something has gone wrong, you still have your backup.


    @copyright: 2005 Thomas Waldmann
    @license: GPL, see COPYING for details
"""

url = 'moinmaster.wikiwikiweb.de/'
destdir = 'underlay'

import sys
sys.path.insert(0, '/org/de.wikiwikiweb.moinmaster/bin15') # farmconfig/wikiconfig location
sys.path.insert(0, '../../..')

import os, os.path, shutil, codecs
from MoinMoin import config
from MoinMoin import wikiutil
from MoinMoin.request import RequestCLI
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.action import AttachFile

def copypage(request, rootdir, pagename):
    """quick and dirty!"""
    pagedir = os.path.join(rootdir, 'pages', wikiutil.quoteWikinameFS(pagename))
    os.makedirs(pagedir)
    
    revstr = '%08d' % 1
    cf = os.path.join(pagedir, 'current')
    open(cf, 'w').write(revstr+'\n')
    
    revdir = os.path.join(pagedir, 'revisions')
    os.makedirs(revdir)
    tf = os.path.join(revdir, revstr)
    p = Page(request, pagename)
    text = p.get_raw_body().replace("\n","\r\n")
    codecs.open(tf, 'wb', config.charset).write(text)

    source_dir = AttachFile.getAttachDir(request, pagename)
    if os.path.exists(source_dir):
        dest_dir = os.path.join(pagedir, "attachments")
        os.makedirs(dest_dir)
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)
            dest_file = os.path.join(dest_dir, filename)
            shutil.copyfile(source_file, dest_file)


request = RequestCLI(url=url)
request.form = request.args = request.setup_args()

pagelist = list(request.rootpage.getPageList(user=''))
for pagename in pagelist:
    copypage(request, destdir, pagename)
    

