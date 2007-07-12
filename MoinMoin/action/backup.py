# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - make or restore a full backup of the wiki

    Triggering backup action will check if you are authorized to do
    a backup and if yes, just send a
    <siteid>-<date>--<time>.tar.<format> to you.

    @copyright: 2005 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, re, time

from MoinMoin import wikiutil
from MoinMoin.support import tarfile

def addFiles(path, tar, exclude):
    """ Add files in path to tar """
    for root, dirs, files in os.walk(path):
        files.sort() # sorted page revs may compress better
        for name in files:
            path = os.path.join(root, name)
            if exclude.search(path):
                continue
            tar.add(path)

def sendBackup(request):
    """ Send compressed tar file """
    dateStamp = time.strftime("%Y-%m-%d--%H-%M-%S-UTC", time.gmtime())
    filename = "%s-%s.tar.%s" % (request.cfg.siteid, dateStamp, request.cfg.backup_compression)
    request.emit_http_headers([
        "Content-Type: application/octet-stream",
        "Content-Disposition: inline; filename=\"%s\"" % filename, ])

    tar = tarfile.open(fileobj=request, mode="w|%s" % request.cfg.backup_compression)
    # allow GNU tar's longer file/pathnames
    tar.posix = False
    exclude = re.compile("|".join(request.cfg.backup_exclude))
    for path in request.cfg.backup_include:
        addFiles(path, tar, exclude)
    tar.close()

def restoreBackup(request, pagename):
    _ = request.getText
    path = request.cfg.backup_storage_dir
    filename = "%s.tar.%s" % (request.cfg.siteid, request.cfg.backup_compression)
    filename = os.path.join(path, filename)
    targetdir = request.cfg.backup_restore_target_dir
    try:
        tar = tarfile.open(fileobj=file(filename), mode="r|%s" % request.cfg.backup_compression)
        # allow GNU tar's longer file/pathnames
        tar.posix = False
        files = []
        dirs = []
        for m in tar:
            if m.isdir():
                dirs.append("%s %s %s" % (m.name, m.size, m.mtime))
            else:
                files.append("%s %s %s" % (m.name, m.size, m.mtime))
            tar.extract(m, targetdir)
        tar.close()
        #files = "<br>".join(files)
        filecount = len(files)
        dircount = len(dirs)
        return sendMsg(request, pagename,
            msg=_('Restored Backup: %(filename)s to target dir: %(targetdir)s.\nFiles: %(filecount)d, Directories: %(dircount)d') %
                locals())
    except:
        return sendMsg(request, pagename, msg=_("Restoring backup: %(filename)s to target dir: %(targetdir)s failed.") % locals())

def sendBackupForm(request, pagename):
    _ = request.getText
    request.emit_http_headers()
    request.setContentLanguage(request.lang)
    title = _('Wiki Backup / Restore')
    request.theme.send_title(title, form=request.form, pagename=pagename)
    request.write(request.formatter.startContent("content"))

    request.write(_("""Some hints:
 * To restore a backup:
  * Restoring a backup will overwrite existing data, so be careful.
  * Rename it to <siteid>.tar.<compression> (remove the --date--time--UTC stuff).
  * Put the backup file into the backup_storage_dir (use scp, ftp, ...).
  * Hit the [[GetText(Restore)]] button below.

 * To make a backup, just hit the [[GetText(Backup)]] button and save the file
   you get to a secure place.

Please make sure your wiki configuration backup_* values are correct and complete.

"""))

    request.write("""
<form action="%(baseurl)s/%(pagename)s" method="POST" enctype="multipart/form-data">
<input type="hidden" name="action" value="backup">
<input type="hidden" name="do" value="backup">
<input type="submit" value="%(backup_button)s">
</form>

<form action="%(baseurl)s/%(pagename)s" method="POST" enctype="multipart/form-data">
<input type="hidden" name="action" value="backup">
<input type="hidden" name="do" value="restore">
<input type="submit" value="%(restore_button)s">
</form>
""" % {
    'baseurl': request.getScriptname(),
    'pagename': wikiutil.quoteWikinameURL(pagename),
    'backup_button': _('Backup'),
    'restore_button': _('Restore'),
})

    request.write(request.formatter.endContent())
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

def sendMsg(request, pagename, msg):
    from MoinMoin import Page
    return Page.Page(request, pagename).send_page(msg=msg)

def backupAllowed(request):
    """ Return True if backup is allowed """
    action = __name__.split('.')[-1]
    user = request.user
    return (action not in request.cfg.actions_excluded and
            user.valid and user.name in request.cfg.backup_users)

def execute(pagename, request):
    _ = request.getText
    if not backupAllowed(request):
        return sendMsg(request, pagename,
                       msg=_('You are not allowed to do remote backup.'))

    dowhat = request.form.get('do', [None])[0]
    if dowhat == 'backup':
        sendBackup(request)
    elif dowhat == 'restore':
        restoreBackup(request, pagename)
    elif dowhat is None:
        sendBackupForm(request, pagename)
    else:
        return sendMsg(request, pagename,
                       msg=_('Unknown backup subaction: %s.') % dowhat)
