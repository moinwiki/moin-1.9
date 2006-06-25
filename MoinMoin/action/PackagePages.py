# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - PackagePages action

    This action allows you to package pages.

    TODO: use ActionBase class

    @copyright: 2005 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import os
import zipfile
from datetime import datetime

from MoinMoin import wikiutil, config, user
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page
from MoinMoin.action.AttachFile import _addLogEntry
from MoinMoin.packages import MOIN_PACKAGE_FILE, packLine, unpackLine

class ActionError(Exception): pass

class PackagePages:
    def __init__(self, pagename, request):
        self.request = request
        self.pagename = pagename
        self.page = Page(request, pagename)

    def allowed(self):
        """ Check if user is allowed to do this. """
        may = self.request.user.may
        return (not self.__class__.__name__ in self.request.cfg.actions_excluded and
                may.write(self.pagename))
    
    def render(self):
        """ Render action

        This action returns a wiki page with optional message, or
        redirects to new page.
        """
        _ = self.request.getText
        form = self.request.form
        
        if form.has_key('cancel'):
            # User canceled
            return self.page.send_page(self.request)

        try:
            if not self.allowed():
                raise ActionError(_('You are not allowed to edit this page.'))
            elif not self.page.exists():
                raise ActionError(_('This page is already deleted or was never created!'))
    
            self.package()
        except ActionError, e:
            return self.page.send_page(self.request, msg=e.args[0])

    def package(self):
        """ Packages pages. """
        _ = self.request.getText
        form = self.request.form
        COMPRESSION_LEVEL = zipfile.ZIP_DEFLATED
        
        # Get new name from form and normalize.
        pagelist = form.get('pagelist', [u''])[0]
        packagename = form.get('packagename', [u''])[0]
        
        if not form.get('submit', [None])[0]:
            raise ActionError(self.makeform())

        pages = []
        for pagename in unpackLine(pagelist, ","):
            pagename = self.request.normalizePagename(pagename)
            if pagename:
                page = Page(self.request, pagename)
                if page.exists() and self.request.user.may.read(pagename):
                    pages.append(page)
        if not pages:
            raise ActionError(self.makeform(_('No pages like "%s"!') % wikiutil.escape(pagelist)))

        pagelist = ', '.join([getattr(page, "page_name") for page in  pages])
        target = wikiutil.taintfilename(packagename)
    
        if not target:
            raise ActionError(self.makeform(_('Invalid filename "%s"!') % wikiutil.escape(packagename)))
        
        # get directory, and possibly create it
        attach_dir = Page(self.request, self.page.page_name).getPagePath("attachments", check_create=1)
        fpath = os.path.join(attach_dir, target).encode(config.charset)
        #print fpath
        if os.path.exists(fpath):
            raise ActionError(_("Attachment '%(target)s' (remote name '%(filename)s') already exists.") % {
                'target': wikiutil.escape(target), 'filename': wikiutil.escape(target)})

        zf = zipfile.ZipFile(fpath, "w", COMPRESSION_LEVEL)

        cnt = 0
        script = [packLine(['MoinMoinPackage', '1']),
                  ]

        for page in pages:
            cnt += 1
            script.append(packLine(["AddRevision", str(cnt), page.page_name, user.getUserIdentification(self.request), "Created by the PackagePages action."]))
            timestamp = wikiutil.version2timestamp(page.mtime_usecs())
            zi = zipfile.ZipInfo(filename=str(cnt), date_time=datetime.fromtimestamp(timestamp).timetuple()[:6])
            zi.compress_type = COMPRESSION_LEVEL
            zf.writestr(zi, page.get_raw_body().encode("utf-8"))
    
        script += [packLine(['Print', 'Thank you for using PackagePages!'])]
    
        zf.writestr(MOIN_PACKAGE_FILE, u"\n".join(script).encode("utf-8"))
        zf.close()

        os.chmod(fpath, 0666 & config.umask)

        _addLogEntry(self.request, 'ATTNEW', self.pagename, target)
        
        raise ActionError(_("Created the package %s containing the pages %s.") % (wikiutil.escape(target), wikiutil.escape(pagelist)))

    def makeform(self, error=""):
        """ Display a rename page form

        The form might contain an error that happened when trying to rename.
        """
        from MoinMoin.widget.dialog import Dialog
        _ = self.request.getText

        error = u'<p class="error">%s</p>\n' % error

        d = {
            'error': error,
            'action': self.__class__.__name__,
            'pagename': wikiutil.escape(self.pagename),
            'package': _('Package pages'),
            'cancel': _('Cancel'),
            'newname_label': _("Package name"),
            'list_label': _("List of page names - separated by a comma"),
        }
        form = '''
%(error)s
<form method="post" action="">
<input type="hidden" name="action" value="%(action)s">
<table>
    <tr>
        <td class="label"><label>%(newname_label)s</label></td>
        <td class="content">
            <input type="text" name="packagename" value="package.zip">
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(list_label)s</label></td>
        <td class="content">
            <input type="text" name="pagelist" maxlength="200">
        </td>
    </tr>
    <tr>
        <td></td>
        <td class="buttons">
            <input type="submit" name="submit" value="%(package)s">
            <input type="submit" name="cancel" value="%(cancel)s">
        </td>
    </tr>
</table>
</form>''' % d
        
        return Dialog(self.request, content=form)        
    
def execute(pagename, request):
    """ Glue code for actions """
    PackagePages(pagename, request).render()
