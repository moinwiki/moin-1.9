# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action macro for page creation from an ascii file or to attach as file 

    MODIFICATION HISTORY:
        @copyright: 2007 by Reimar Bauer 
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

    def is_allowed(self):
        # this is not strictly necessary because the underlying storage code checks
        # as well
        may = self.request.user.may
        return may.write(self.pagename) and may.delete(self.pagename)

    def check_condition(self):
        _ = self._
        if not self.page.exists():
            return _("You are not allowed to change this page.")
        else:
            return None

    def do_action(self):
        """ Load """
        status = False
        _ = self._
        form = self.form
        author = self.request.user.name

        rename = form.get('rename', [u''])[0]
        filename = None
        if form.has_key('file__filename__'):
            filename = form['file__filename__']

        filecontent = form['file'][0]
        bytes = len(filecontent)

        # find if attachment is necessary
        ascii = True
        for char in filecontent[:-1]:
            if not ord(char) < 128:
                ascii = False
                break

        overwrite = 0
        if form.has_key('overwrite'):
            try:
                overwrite = int(request.form['overwrite'][0])
            except:
                pass

        target = filename
        if rename:
            target = wikiutil.clean_comment(rename.strip())

        # preprocess the filename
        # strip leading drive and path (IE misbehaviour)
        if len(target) > 1 and (target[1] == ':' or target[0] == '\\'): # C:.... or \path... or \\server\...
            bsindex = target.rfind('\\')
            if bsindex >= 0:
                target = target[bsindex+1:]

        msg = ''
        if self.request.form.has_key('attachment') or not ascii:
            attach_dir = AttachFile.getAttachDir(self.request, self.pagename, create=1)
            fpath = os.path.join(attach_dir, target).encode(config.charset)
            exists = os.path.exists(fpath)

            if exists and not overwrite:
                msg = _("Attachment '%(target)s' (remote name '%(filename)s') already exists.") % {
                         'target': target, 'filename': filename}
            if exists:
                try:
                    os.remove(fpath)
                except:
                    pass

            AttachFile.add_attachment(self.request, self.pagename, target, filecontent)
            bytes = len(filecontent)
            msg = _("Attachment '%(target)s' (remote name '%(filename)s') with %(bytes)d bytes saved.") % {
                   'target': target, 'filename': filename, 'bytes': bytes}
            status = True
        else:
            page = PageEditor(self.request, target, do_editor_backup=0, uid_override=author)
            try:
                page.saveText(filecontent, 0)
                msg = _("%(pagename)s added") % {"pagename": self.pagename}
                status = True
                self.pagename = target
            except PageEditor.Unchanged:
                pass
            page.clean_acl_cache()
        return status, msg

    def do_action_finish(self, success):
        if success:
            url = Page(self.request, self.pagename).url(self.request, escape=0, relative=False)
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

