# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - DeletePage action

    This action allows you to delete a page.

    @copyright: 2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os
from MoinMoin import config, wikiutil
from MoinMoin.PageEditor import PageEditor


def execute(pagename, request):
    _ = request.getText
    actname = __name__.split('.')[-1]
    # Create a page editor that does not do editor backups, because
    # delete generates a "deleted" version of the page.
    page = PageEditor(request, pagename, do_editor_backup=0)

    # be extra paranoid in dangerous actions
    if actname in request.cfg.actions_excluded \
            or not request.user.may.write(pagename) \
            or not request.user.may.delete(pagename):
        return page.send_page(request,
            msg = _('You are not allowed to delete this page.'))

    # check whether page exists at all
    if not page.exists():
        return page.send_page(request,
            msg = _('This page is already deleted or was never created!'))

    # check whether the user clicked the delete button
    if request.form.has_key('button') and request.form.has_key('ticket'):
        # check whether this is a valid deletion request (make outside
        # attacks harder by requiring two full HTTP transactions)
        if not wikiutil.checkTicket(request.form['ticket'][0]):
            return page.send_page(request,
                msg = _('Please use the interactive user interface to delete pages!'))

        # Delete the page
        comment = request.form.get('comment', [u''])[0]
        comment = wikiutil.clean_comment(comment)
        msg = page.deletePage(comment)

        return page.send_page(request, msg=msg)

    # send deletion form
    ticket = wikiutil.createTicket()
    querytext = _('Really delete this page?')
    button = _('Delete')
    comment_label = _("Optional reason for the deletion")

    # TODO: this form sucks, redesign like RenamePage
    formhtml = '''
<form method="post" action="">
<strong>%(querytext)s</strong>
<input type="hidden" name="action" value="%(actname)s">
<input type="hidden" name="ticket" value="%(ticket)s">
<input type="submit" name="button" value="%(button)s">
<p>
%(comment_label)s<br>
<input type="text" name="comment" size="60" maxlength="80">
</form>''' % {
    'querytext': querytext,
    'actname': actname,
    'ticket': ticket,
    'button': button,
    'comment_label': comment_label,
}

    return page.send_page(request, msg=formhtml)

