#!/usr/bin/env python
"""
    MoinMoin - migrate from several twikidraw files to one tarfile.

    This script looks at all pages' attachments and checks whether they
    contain TWikiDraw items. If this is the case, the TWikiDraw items are
    transformed into a single tarfile on the disk.
    (The intention is to later store this as a single Item in the new storage
    layer.)

    @copyright: 2008 by Christopher Denter
    @license: GNU GPL, see COPYING for details.

"""

import os
import tarfile

from MoinMoin.action.AttachFile import getAttachDir


def execute(script, data_dir, rev):
    pagenames = script.request.rootpage.getPageList(user='', include_underlay=False)

    for pagename in pagenames:
        attachdir = getAttachDir(script.request, pagename)
        try:
           filenames = os.listdir(attachdir)
        except OSError:
            # silenced. attachment directory does not exist. proceed with next page
            continue
        for filename in filenames:
            if filename.endswith('.draw'):
                filename = filename.split('.')[0]  # XXX only 1 dot in filename allowed atm
                # Open for uncompressed writing
                os.chdir(attachdir)  # XXX Do we really need to catch permission errors here?
                tar = tarfile.open(filename + '.tar', 'w:')  # XXX same question here.
                tar.add(filename + '.draw')
                os.remove(filename + '.draw')  # XXX and here
                try:
                    tar.add(filename + '.map')
                    os.remove(filename + '.map')  # XXX and here
                except OSError:
                    # The .map file is optional
                    pass

                # TODO Decide whether png files shall be included in the
                # TODO tar file and take appropriate action.

                tar.close()

    return 1090000
