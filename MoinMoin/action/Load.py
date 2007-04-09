# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action macro for page creation from file or attach file to current page

    @copyright: 2007 Reimar Bauer 
    @license: GNU GPL, see COPYING for details.
"""
import os
from MoinMoin import wikiutil, config
from MoinMoin.action import ActionBase, AttachFile
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page

class Load(ActionBase):
    """ Load page action

    Note: the action name is the class name
    """
    def __init__(self, pagename, request):
        ActionBase.__init__(self, pagename, request)
        self.use_ticket = True
        _ = self._
        self.form_trigger = 'Load'
        self.form_trigger_label = _('Load')
        self.pagename = pagename
        self.method = 'POST'
        self.enctype = 'multipart/form-data'

    def do_action(self):
        """ Load """
        status = False
        _ = self._
        form = self.form
        author = self.request.user.name

        rename = form.get('rename', [u''])[0]

        filename = None
        if 'file__filename__' in form:
            filename = form['file__filename__']

        filecontent = form['file'][0]
        bytes = len(filecontent)

        overwrite = False
        if 'overwrite' in form:
            overwrite = True

        target = filename
        if rename:
            target = wikiutil.clean_input(rename.strip())

        # preprocess the filename
        # strip leading drive and path (IE misbehaviour)
        if len(target) > 1 and (target[1] == ':' or target[0] == '\\'): # C:.... or \path... or \\server\...
            bsindex = target.rfind('\\')
            if bsindex >= 0:
                target = target[bsindex+1:]

        if 'attachment' in self.request.form and self.request.user.may.write(self.pagename):
            attach_dir = AttachFile.getAttachDir(self.request, self.pagename, create=1)
            fpath = os.path.join(attach_dir, target).encode(config.charset)
            exists = os.path.exists(fpath)
            if exists and not overwrite:
                msg = _("Attachment '%(target)s' (remote name '%(filename)s') already exists.") % {
                         'target': target, 'filename': filename}
                return status, msg

            if exists and self.request.user.may.delete(self.pagename):
                try:
                    os.remove(fpath)
                except:
                    pass
            else:
                msg = _("You are not allowed to delete attachments on this page.")
                return status, msg

            AttachFile.add_attachment(self.request, self.pagename, target, filecontent)
            bytes = len(filecontent)
            msg = _("Attachment '%(target)s' (remote name '%(filename)s') with %(bytes)d bytes saved.") % {
                   'target': target, 'filename': filename, 'bytes': bytes}
            status = True

        else:
            filecontent = unicode(filecontent, config.charset)
            self.pagename = wikiutil.escape(target)
            page = Page(self.request, self.pagename)
            pagedir = page.getPagePath("", check_create=0)
            rev = Page.get_current_from_pagedir(page, pagedir)
            pg = PageEditor(self.request, self.pagename, do_editor_backup=0, uid_override=author)
            try:
                msg = pg.saveText(filecontent, rev)
                status = True
            except pg.EditConflict, e:
                msg = e.message
            except pg.SaveError, msg:
                msg = unicode(msg)

        return status, msg

    def do_action_finish(self, success):
        if success:
            url = Page(self.request, self.pagename).url(self.request, relative=False)
            self.request.http_redirect(url)
            self.request.finish()
        else:
            self.render_msg(self.make_form())

    def get_form_html(self, buttons_html):
        _ = self._
        return """
%(querytext_pages)s
<dl>
<dt>%(upload_label_file)s</dt>
<dd><input type="file" name="file" size="50" value=""></dd>
<dt>%(upload_label_rename)s</dt>
<dd><input type="text" name="rename" size="50" value=""></dd>
%(querytext_attachment)s
<dt>%(upload)s <input type="checkbox" name="attachment" value="off">
%(overwrite)s <input type="checkbox" name="overwrite" value="off"></dt>
</dl>
<p>
<input type="hidden" name="action" value="%(action_name)s">
<input type="hidden" name="do" value="upload">
</p>
<td class="buttons">
%(buttons_html)s
</td>""" % {
    'querytext_pages': '<h2>' + _("New Page or New Attachment") + '</h2><p>' +
_("""You can upload a file to a new page or choose to upload a file as attachment for the current page""") + '</p>',
    'querytext_attachment': '<h2>' + _("New Attachment") + '</h2><p>' +
_("""An upload will never overwrite an existing file. If there is a name
conflict, you have to rename the file that you want to upload.
Otherwise, if "Rename to" is left blank, the original filename will be used.""") + '</p>',
    'buttons_html': buttons_html,
    'upload': _('attachment'),
    'overwrite': _('overwrite'),
    'action_name': self.form_trigger,
    'upload_label_file': _('Upload'),
    'upload_label_rename': _('New Name'),
}

def execute(pagename, request):
    """ Glue code for actions """
    Load(pagename, request).render()

