#!/usr/bin/env python
"""
    MoinMoin - migrate from several twikidraw files to one tarfile.

    This script looks at all pages' attachments and checks whether they
    contain TWikiDraw items. If this is the case, the TWikiDraw items are
    bundled into a single tar file (.tdraw) on the disk.
    (The intention is to later store this as a single Item in the new storage
    layer.)

    @copyright: 2008 by Christopher Denter
    @license: GNU GPL, see COPYING for details.

"""

import os, errno

from MoinMoin.support import tarfile
from MoinMoin.action.AttachFile import getAttachDir


def execute(script, data_dir, rev):
    pagenames = script.request.rootpage.getPageList(user='', include_underlay=False)

    for pagename in pagenames:
        attachdir = getAttachDir(script.request, pagename)
        try:
            drawings = [fn for fn in os.listdir(attachdir) if fn.endswith('.draw')]
        except OSError:
            # silenced. attachment directory does not exist. proceed with next page
            continue
        for drawing in drawings:
            basename = os.path.splitext(drawing)[0]
            tar_filename = os.path.join(attachdir, basename + '.tdraw')
            tar = tarfile.open(tar_filename, 'w:')
            for ext in ['.draw', '.map', '.png', '.gif', ]:
                filename = os.path.join(attachdir, basename + ext)
                try:
                    if ext != '.gif':
                        # get rid of the gif (TWikiDraw will (re)create
                        # a .png when someone edits the drawing)
                        # we use drawing.* as tar member filenames EVER, so the
                        # member filenames do not need to be changed when the
                        # tar container file gets renamed:
                        tar.add(filename, 'drawing' + ext)
                    os.remove(filename)
                except OSError, err:
                    if err.errno != errno.ENOENT:
                        # .map and .png are optional, .draw should be there
                        raise
            tar.close()

    return 1090000

