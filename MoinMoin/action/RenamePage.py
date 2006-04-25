# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RenamePage action

    This action allows you to rename a page.

    Based on the DeletePage action by Jürgen Hermann <jh@web.de>

    @copyright: 2002-2004 Michael Reinsch <mr@uue.org>
    @license: GNU GPL, see COPYING for details.
"""

import os
from MoinMoin import wikiutil
from MoinMoin.PageEditor import PageEditor

class RenamePage:
    """ Rename page action

    Note: the action name is the class name
    """
    def __init__(self, pagename, request):
        self.request = request
        self.pagename = pagename
        self.page = PageEditor(request, pagename)
        self.newpage = None
        self.error = ''

    def allowed(self):
        """ Check if user is allowed to do this

        This could be a standard method of the base action class, doing
        the filtering by action class name and cfg.actions_excluded.
        """
        may = self.request.user.may
        return (not self.__class__.__name__ in self.request.cfg.actions_excluded and
                may.write(self.pagename) and may.delete(self.pagename))
    
    def render(self):
        """ Render action

        This action return a wiki page with optional message, or
        redirect to new page.
        """
        _ = self.request.getText
        form = self.request.form
        
        if form.has_key('cancel'):
            # User canceled
            return self.page.send_page(self.request)

        # Validate user rights and page state. If we get error here, we
        # return an error message, without the rename form.
        error = None
        if not self.allowed():
            error = _('You are not allowed to rename pages in this wiki!')
        elif not self.page.exists():
            error = _('This page is already deleted or was never created!')
        if error:
            # Send page with an error message
            return self.page.send_page(self.request, msg=error)

        # Try to rename. If we get an error here, we return the error
        # message with a rename form.
        elif (form.has_key('rename') and form.has_key('newpagename') and
              form.has_key('ticket')):
            # User replied to the rename form with all required items
            self.rename()
            if not self.error:
                self.request.http_redirect(self.newpage.url(self.request))
                return self.request.finish()    

        # A new form request, or form has missing data, or rename
        # failed. Return a new form with optional error.
        return self.page.send_page(self.request, msg=self.makeform())

    def rename(self):
        """ Rename pagename and return the new page """
        _ = self.request.getText
        form = self.request.form
        
        # Require a valid ticket. Make outside attacks harder by
        # requiring two full HTTP transactions
        if not wikiutil.checkTicket(form['ticket'][0]):
            self.error = _('Please use the interactive user interface to rename pages!')
            return

        # Get new name from form and normalize.
        comment = form.get('comment', [u''])[0]
        comment = wikiutil.clean_comment(comment)
        newpagename = form.get('newpagename')[0]
        newpagename = self.request.normalizePagename(newpagename)

        # Name might be empty after normalization. To save translation
        # work for this extreme case, we just use "EmptyName".
        if not newpagename:
            newpagename = "EmptyName"

        # Valid new name
        newpage = PageEditor(self.request, newpagename)

        # Check whether a page with the new name already exists
        if newpage.exists(includeDeleted=1):
            return self.pageExistsError(newpagename)
        
        # Get old page text
        savetext = self.page.get_raw_body()

        oldpath = self.page.getPagePath(check_create=0)
        newpath = newpage.getPagePath(check_create=0)

        # Rename page

        # NOTE: might fail if another process created newpagename just
        # NOW, while you read this comment. Rename is atomic for files -
        # but for directories, rename will fail if the directory
        # exists. We should have global edit-lock to avoid this.
        # See http://docs.python.org/lib/os-file-dir.html
        try:
            os.rename(oldpath, newpath)
            self.newpage = newpage
            self.error = None
            # Save page text with a comment about the old name
            savetext = u"## page was renamed from %s\n%s" % (self.pagename, savetext)
            newpage.saveText(savetext, 0, comment=comment)
        except OSError, err:
            # Try to understand what happened. Maybe its better to check
            # the error code, but I just reused the available code above...
            if newpage.exists(includeDeleted=1):
                return self.pageExistsError(newpagename)
            else:
                self.error = _('Could not rename page because of file system'
                             ' error: %s.') % unicode(err)
                        
    def makeform(self):
        """ Display a rename page form

        The form might contain an error that happened when trying to rename.
        """
        from MoinMoin.widget.dialog import Dialog
        _ = self.request.getText

        error = ''
        if self.error:
            error = u'<p class="error">%s</p>\n' % self.error

        d = {
            'error': error,
            'action': self.__class__.__name__,
            'ticket': wikiutil.createTicket(),
            'pagename': self.pagename,
            'rename': _('Rename Page'),
            'cancel': _('Cancel'),
            'newname_label': _("New name"),
            'comment_label': _("Optional reason for the renaming"),
        }
        form = '''
%(error)s
<form method="post" action="">
<input type="hidden" name="action" value="%(action)s">
<input type="hidden" name="ticket" value="%(ticket)s">
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
            <input type="text" name="comment" maxlength="80">
        </td>
    </tr>
    <tr>
        <td></td>
        <td class="buttons">
            <input type="submit" name="rename" value="%(rename)s">
            <input type="submit" name="cancel" value="%(cancel)s">
        </td>
    </tr>
</table>
</form>''' % d
        
        return Dialog(self.request, content=form)        
    
    def pageExistsError(self, pagename):
        _ = self.request.getText
        self.error = _("""'''A page with the name {{{'%s'}}} already exists.'''

Try a different name.""") % (pagename,)    

    
def execute(pagename, request):
    """ Glue code for actions """
    RenamePage(pagename, request).render()
    
