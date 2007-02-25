# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RenamePage action

    This action allows you to rename a page.

    @copyright: 2002-2004 Michael Reinsch <mr@uue.org>,
                2006 MoinMoin:ThomasWaldmann
                2007 ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""
import re
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
        filterfn = re.compile(pagename).match
        pages = request.rootpage.getPageList(user='', exists=1, filter=filterfn)
        self.subpages = []
        subpage = pagename + '/'
        for name in pages:
            if name.startswith(subpage) and self.request.user.may.delete(name):
                self.subpages.append(name)

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

        rename_subpages = 0
        if form.has_key('rename_subpages'):
            try:
                rename_subpages = int(form['rename_subpages'][0])
            except:
                pass

        if rename_subpages and self.subpages:
            for name in self.subpages:
                self.page = PageEditor(self.request, name)
                new_subpagename = name.replace(self.pagename, newpagename, 1)
                success_i, msg = self.page.renamePage(new_subpagename, comment)

        self.newpagename = newpagename # keep there for finish
        return success, msg

    def do_action_finish(self, success):
        if success:
            url = Page(self.request, self.newpagename).url(self.request, relative=False)
            self.request.http_redirect(url)
            self.request.finish()
        else:
            self.render_msg(self.make_form())

    def get_form_html(self, buttons_html):
        _ = self._
        if self.subpages:
            subpages = ' '.join(self.subpages)

            d = {
                'subpage': subpages,
                'subpages_checked':('', 'checked')[self.request.form.get('subpages_checked', ['0'])[0] == '1'],
                'subpage_label': _('Rename all /subpages too?'),
                'pagename': wikiutil.escape(self.pagename),
                'newname_label': _("New name"),
                'comment_label': _("Optional reason for the renaming"),
                'buttons_html': buttons_html,
                'querytext': _('Really rename this page?')
                }

            return '''
<strong>%(querytext)s</strong>
<br>
<br>
<table>
    <tr>
    <dd>
        %(subpage_label)s<input type="checkbox" name="rename_subpages" value="1" %(subpages_checked)s> 
    </dd>
    <dd>
        <class="label"><subpage> %(subpage)s</subpage>
    </dd>   
    </tr>
</table>       
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
        
        else:
            d = {
                'pagename': wikiutil.escape(self.pagename),
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

