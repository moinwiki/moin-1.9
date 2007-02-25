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
        pages = request.rootpage.getPageList(user='', exists='')
        self.subpages = []
        subpage = pagename + '/'
        for name in pages:
            if name.startswith(subpage) and self.request.user.may.delete(name):
                self.subpages.append(name)
                

    def is_allowed(self):
        # this is not strictly necessary because the underlying storage code checks
        # as well
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
        msgs = msg
        delete_subpages = 0
        if form.has_key('delete_subpages'):
            try:
                delete_subpages = int(form['delete_subpages'][0])
            except:
                pass

        if delete_subpages and self.subpages:
            for name in self.subpages:
                self.page = PageEditor(self.request, name, do_editor_backup=0)
                success_i, msg = self.page.deletePage(comment)
                msgs += "%s " %msg

        return success, msgs

    def get_form_html(self, buttons_html):
        _ = self._

        if self.subpages:
            subpages = ' '.join(self.subpages)

            d = {
                'subpage': subpages,
                'subpages_checked':('', 'checked')[self.request.form.get('subpages_checked', ['0'])[0] == '1'],
                'subpage_label': _('Delete all /subpages too?'),
                'comment_label': _("Optional reason for the deletion"),
                'buttons_html': buttons_html,
                'querytext': _('Really delete this page?'),
                }

            return '''
<strong>%(querytext)s</strong>
<br>
<br>
<table>
<tr>
<dd>
%(subpage_label)s<input type="checkbox" name="delete_subpages" value="1" %(subpages_checked)s> </dd>
<dd><class="label"><subpage> %(subpage)s</subpage></dd>   
</tr>
</table>
<table>
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

        else:
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
    DeletePage(pagename, request).render()

