# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action to load page content from a file upload

    @copyright: 2007-2008 MoinMoin:ReimarBauer,
                2008 MoinMoin:ThomasWaldmann
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
        request = self.request

        comment = form.get('comment', [u''])[0]
        comment = wikiutil.clean_input(comment)

        filename = form.get('file__filename__')
        rename = form.get('rename', [''])[0].strip()
        if rename:
            target = rename
        else:
            target = filename

        target = AttachFile.preprocess_filename(target)
        target = wikiutil.clean_input(target)

        if target:
            filecontent = form['file'][0]
            if hasattr(filecontent, 'read'): # a file-like object
                filecontent = filecontent.read() # XXX reads complete file into memory!
            filecontent = wikiutil.decodeUnknownInput(filecontent)

            self.pagename = target
            pg = PageEditor(request, self.pagename)
            try:
                msg = pg.saveText(filecontent, 0, comment=comment)
                status = True
            except pg.EditConflict, e:
                msg = e.message
            except pg.SaveError, msg:
                msg = unicode(msg)
        else:
            msg = _("Pagename not specified!")
        return status, msg

    def do_action_finish(self, success):
        if success:
            url = Page(self.request, self.pagename).url(self.request)
            self.request.http_redirect(url)
        else:
            self.render_msg(self.make_form(), "dialog")

    def get_form_html(self, buttons_html):
        _ = self._
        return """
<h2>%(headline)s</h2>
<p>%(explanation)s</p>
<dl>
<dt>%(upload_label_file)s</dt>
<dd><input type="file" name="file" size="50" value=""></dd>
<dt>%(upload_label_rename)s</dt>
<dd><input type="text" name="rename" size="50" value="%(pagename)s"></dd>
<dt>%(upload_label_comment)s</dt>
<dd><input type="text" name="comment" size="80" maxlength="200"></dd>
</dl>
<p>
<input type="hidden" name="action" value="%(action_name)s">
<input type="hidden" name="do" value="upload">
</p>
<td class="buttons">
%(buttons_html)s
</td>""" % {
    'headline': _("Upload page content"),
    'explanation': _("You can upload content for the page named below. "
                     "If you change the page name, you can also upload content for another page. "
                     "If the page name is empty, we derive the page name from the file name."),
    'upload_label_file': _('File to load page content from'),
    'upload_label_comment': _('Comment'),
    'upload_label_rename': _('Page Name'),
    'pagename': self.pagename,
    'buttons_html': buttons_html,
    'action_name': self.form_trigger,
}

def execute(pagename, request):
    """ Glue code for actions """
    Load(pagename, request).render()

