# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RenamePage action

    This action allows you to rename a page.

    @copyright: 2002-2004 Michael Reinsch <mr@uue.org>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os
from MoinMoin import wikiutil
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.action import ActionBase

class RenamePage(ActionBase):
    """ Rename page action

    Note: the action name is the class name
    """
    def __init__(self, pagename, request):
        ActionBase.__init__(self, pagename, request)
        self.use_ticket = True
        _ = self._
        self.form_trigger = 'rename'
        self.form_trigger_label = _('Rename Page')

    def is_allowed(self):
        may = self.request.user.may
        return may.write(self.pagename) and may.delete(self.pagename)

    def check_condition(self):
        _ = self._
        if not self.page.exists():
            return _('This page is already deleted or was never created!')
        else:
            return None

    def do_action(self):
        """ Rename this page to "pagename" """
        _ = self._
        form = self.form
        newpagename = form.get('newpagename', [u''])[0]
        newpagename = self.request.normalizePagename(newpagename)
        comment = form.get('comment', [u''])[0]
        comment = wikiutil.clean_comment(comment)

        self.page = PageEditor(self.request, self.pagename)
        success, msg = self.page.renamePage(newpagename, comment)
        self.newpagename = newpagename # keep there for finish
        return success, msg

    def do_action_finish(self, success):
        if success:
            url = Page(self.request, self.newpagename).url(self.request)
            self.request.http_redirect(url)
            self.request.finish()
        else:
            self.render_msg(self.make_form())

    def get_form_html(self, buttons_html):
        _ = self._
        d = {
            'pagename': self.pagename,
            'newname_label': _("New name"),
            'comment_label': _("Optional reason for the renaming"),
            'buttons_html': buttons_html,
        }
        return '''
<table>
    <tr>
        <td class="label"><label>%(newname_label)s</label></td>
        <td class="content">
            <input type="text" name="newpagename" value="%(pagename)s">
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(comment_label)s</label></td>
        <td class="content">
            <input type="text" name="comment" maxlength="200">
        </td>
    </tr>
    <tr>
        <td></td>
        <td class="buttons">
            %(buttons_html)s
        </td>
    </tr>
</table>
''' % d

def execute(pagename, request):
    """ Glue code for actions """
    RenamePage(pagename, request).render()

