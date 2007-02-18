# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - revert a page to a previous revision

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.Page import Page

def execute(pagename, request):
    """ restore another revision of a page as a new current revision """
    from MoinMoin.PageEditor import PageEditor
    _ = request.getText

    if not request.user.may.revert(pagename):
        return Page(request, pagename).send_page(
            msg=_('You are not allowed to revert this page!'))

    rev = request.rev
    revstr = '%08d' % rev
    oldpg = Page(request, pagename, rev=rev)
    pg = PageEditor(request, pagename)

    try:
        savemsg = pg.saveText(oldpg.get_raw_body(), 0, extra=revstr,
                              action="SAVE/REVERT")
    except pg.SaveError, msg:
        # msg contain a unicode string
        savemsg = unicode(msg)
    request.reset()
    pg.send_page(msg=savemsg)

