# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - make a full backup of the wiki

    Triggering WikiBackup action will check if you are authorized to do a
    backup and if yes, just send a <siteid>-<date>--<time>.tgz to you.

    @copyright: 2005 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, re, time
import tarfile, gzip
from MoinMoin.util import MoinMoinNoFooter

GZCOMPRESSLEVEL = 5 # TODO: look what level is best for us

def send_backup(request):
    gzfileobj = gzip.GzipFile(fileobj=request, mode="wb", compresslevel=GZCOMPRESSLEVEL)
    tarfileobj = tarfile.TarFile(fileobj=gzfileobj, mode="w")
    tarfileobj.posix = False # allow GNU tar's longer file/pathnames

    exclude_re = re.compile("|".join(request.cfg.backup_exclude))
    for path in request.cfg.backup_include:
        for root, dirs, files in os.walk(path):
            for fname in files:
                fpath = os.path.join(root, fname)
                if not exclude_re.search(fpath):
                    fileobj = open(fpath, "rb")
                    tarinfo = tarfileobj.gettarinfo(fileobj=fileobj)
                    tarfileobj.addfile(tarinfo, fileobj)
                    fileobj.close()

    tarfileobj.close()
    gzfileobj.close()

def execute(pagename, request):
    _ = request.getText
    # be extra paranoid in dangerous actions
    actname = __name__.split('.')[-1]
    if actname in request.cfg.actions_excluded or \
            request.user.name not in request.cfg.backup_users:
        return Page.Page(request, pagename).send_page(request,
            msg = _('You are not allowed to use this action.'))

    datestr = time.strftime("%Y-%m-%d--%H-%M-%SUTC", time.gmtime())
    backupfilename = "%s-%s.tgz" % (request.cfg.siteid, datestr)
    request.http_headers([
        "Content-Type: application/octet-stream", # we could also use some more tgz specific
        "Content-Disposition: inline; filename=\"%s\"" % backupfilename,
    ])

    send_backup(request)

    raise MoinMoinNoFooter

