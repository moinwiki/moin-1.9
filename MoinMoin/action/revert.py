# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - revert a page to a previous revision

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.Page import Page

def execute(pagename, request):
    """ restore another revision of a page as a new current revision """
    from MoinMoin.PageEditor import PageEditor
    _ = request.getText
    msg = None
    rev = request.rev
    pg = Page(request, pagename, rev=rev)

    if not request.user.may.revert(pagename):
        msg = _('You are not allowed to revert this page!')
    elif rev is None:
        msg = _('You were viewing the current revision of this page when you called the revert action. '
                'If you want to revert to an older revision, first view that older revision and '
                'then call revert to this (older) revision again.')
    else:
        newpg = PageEditor(request, pagename)

        revstr = '%08d' % rev
        try:
            msg = newpg.saveText(pg.get_raw_body(), 0, extra=revstr, action="SAVE/REVERT")
            pg = newpg
        except newpg.SaveError, msg:
            msg = unicode(msg)
        request.reset()

        key = request.form.get('key', ['text_html'])[0]

        # Remove cache entry (if exists)
        pg = Page(request, pagename)
        from MoinMoin import caching
        caching.CacheEntry(request, pg, key, scope='item').remove()
        caching.CacheEntry(request, pg, "pagelinks", scope='item').remove()

        # Notify observers
        from MoinMoin.events import PageRevertedEvent, send_event
        e = PageRevertedEvent(request, pagename, request.rev, revstr)
        send_event(e)

    pg.send_page(msg=msg)
