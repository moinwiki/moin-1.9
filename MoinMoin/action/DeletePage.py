# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - DeletePage action

    This action allows you to delete a page.

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.PageEditor import PageEditor
from MoinMoin.action import ActionBase

class DeletePage(ActionBase):
    """ Delete page action

    Note: the action name is the class name
    """
    def __init__(self, pagename, request):
        ActionBase.__init__(self, pagename, request)
        self.use_ticket = True
        _ = self._
        self.form_trigger = 'delete'
        self.form_trigger_label = _('Delete')

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
        """ Delete pagename """
        form = self.form
        comment = form.get('comment', [u''])[0]
        comment = wikiutil.clean_comment(comment)
        
        # Create a page editor that does not do editor backups, because
        # delete generates a "deleted" version of the page.
        self.page = PageEditor(self.request, self.pagename, do_editor_backup=0)
        success, msg = self.page.deletePage(comment)
        return success, msg

    def get_form_html(self, buttons_html):
        _ = self._
        d = {
            'pagename': self.pagename,
            'comment_label': _("Optional reason for the deletion"),
            'buttons_html': buttons_html,
            'querytext': _('Really delete this page?'),
        }
        return '''
<strong>%(querytext)s</strong>
<table>
    <tr>
        <td class="label"><label>%(comment_label)s</label></td>
        <td class="content">
            <input type="text" name="comment" maxlength="80">
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
    DeletePage(pagename, request).render()

