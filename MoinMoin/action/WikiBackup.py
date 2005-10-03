# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - make a full backup of the wiki

    Triggering WikiBackup action will check if you are authorized to do
    a backup and if yes, just send a
    <siteid>-<date>--<time>.tar.<format> to you.

    @copyright: 2005 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, re, time, tarfile
from MoinMoin.util import MoinMoinNoFooter


defaultCompression = 'gz'
compressionOptions = ['gz', 'bz2']


def addFiles(path, tar, exclude):
    """ Add files in path to tar """
    for root, dirs, files in os.walk(path):
        files.sort() # sorted page revs may compress better
        for name in files:
            path = os.path.join(root, name)
            if exclude.search(path):
                continue
            tar.add(path)
    

def sendBackup(request, compression='gz'):
    """ Send compressed tar file """    
    tar = tarfile.open(fileobj=request, mode="w|%s" % compression)
    # allow GNU tar's longer file/pathnames 
    tar.posix = False           
    exclude = re.compile("|".join(request.cfg.backup_exclude))
    
    for path in request.cfg.backup_include:
        addFiles(path, tar, exclude)
    
    tar.close()


def sendError(request, pagename, msg):
    from MoinMoin import Page
    return Page.Page(request, pagename).send_page(request, msg=msg)    


def backupAllowed(request):
    """ Return True if backup is allowed """
    action = __name__.split('.')[-1]
    user = request.user
    return (action not in request.cfg.actions_excluded and
            user.valid and user.name in request.cfg.backup_users)


def execute(pagename, request):
    _ = request.getText
    if not backupAllowed(request):        
        return sendError(request, pagename, 
                         msg=_('You are not allowed to do remote backup.'))

    compression = request.form.get('format', [defaultCompression])[0]
    if compression not in compressionOptions:
        return sendError(request, pagename, 
                         msg=_('Unknown backup format: %s.' % compression))
    
    dateStamp = time.strftime("%Y-%m-%d--%H-%M-%S-UTC", time.gmtime())
    filename = "%s-%s.tar.%s" % (request.cfg.siteid, dateStamp, compression)
    
    request.http_headers([
        # TODO: use more specific tar gz/bz2 content type?
        "Content-Type: application/octet-stream", 
        "Content-Disposition: inline; filename=\"%s\"" % filename,])

    sendBackup(request, compression)

    raise MoinMoinNoFooter

