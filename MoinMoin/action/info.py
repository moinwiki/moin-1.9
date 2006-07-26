# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - info action

    Displays page history, some general page infos and statistics.

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import os

from MoinMoin import config, wikiutil, action
from MoinMoin.Page import Page
from MoinMoin.logfile import editlog

def execute(pagename, request):
    """ show misc. infos about a page """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return

    def general(page, pagename, request):
        _ = request.getText

        request.write('<h2>%s</h2>\n' % _('General Information'))

        # show page size
        request.write(("<p>%s</p>" % _("Page size: %d")) % page.size())

        # show SHA digest fingerprint
        import sha
        digest = sha.new(page.get_raw_body().encode(config.charset)).hexdigest().upper()
        request.write('<p>%(label)s <tt>%(value)s</tt></p>' % {
            'label': _("SHA digest of this page's content is:"),
            'value': digest,
            })

        # show attachments (if allowed)
        attachment_info = action.getHandler(request, 'AttachFile', 'info')
        if attachment_info:
            request.write(attachment_info(pagename, request))

        # show subscribers
        subscribers = page.getSubscribers(request, include_self=1, return_users=1)
        if subscribers:
            request.write('<p>', _('The following users subscribed to this page:'))
            for lang in subscribers.keys():
                request.write('<br>[%s] ' % lang)
                for user in subscribers[lang]:
                    # do NOT disclose email addr, only WikiName
                    userhomepage = Page(request, user.name)
                    if userhomepage.exists():
                        request.write(userhomepage.link_to(request) + ' ')
                    else:
                        request.write(user.name + ' ')
            request.write('</p>')

        # show links
        links = page.getPageLinks(request)
        if links:
            request.write('<p>', _('This page links to the following pages:'), '<br>')
            for linkedpage in links:
                request.write("%s%s " % (Page(request, linkedpage).link_to(request), ",."[linkedpage == links[-1]]))
            request.write("</p>")

    def history(page, pagename, request):
        # show history as default
        _ = request.getText

        # open log for this page
        from MoinMoin.util.dataset import TupleDataset, Column

        history = TupleDataset()
        history.columns = [
            Column('rev', label='#', align='right'),
            Column('mtime', label=_('Date'), align='right'),
            Column('size', label=_('Size'), align='right'),
            Column('diff', label='<input type="submit" value="%s">' % (_("Diff"))),
            Column('editor', label=_('Editor'), hidden=not request.cfg.show_names),
            Column('comment', label=_('Comment')),
            Column('action', label=_('Action')),
            ]

        # generate history list
        revisions = page.getRevList()
        versions = len(revisions)

        may_revert = request.user.may.revert(pagename)

        # read in the complete log of this page
        log = editlog.EditLog(request, rootpagename=pagename)
        count = 0
        for line in log.reverse():
            rev = int(line.rev)
            actions = ""
            if line.action in ['SAVE', 'SAVENEW', 'SAVE/REVERT', ]:
                size = page.size(rev=rev)
                if count == 0: # latest page
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('view'),
                        querystr=''))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('raw'),
                        querystr='action=raw', rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('print'),
                        querystr='action=print', rel='nofollow'))
                else:
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('view'),
                        querystr='action=recall&rev=%d' % rev, rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('raw'),
                        querystr='action=raw&rev=%d' % rev, rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('print'),
                        querystr='action=print&rev=%d' % rev, rel='nofollow'))
                    if may_revert and size: # you can only revert to nonempty revisions
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('revert'),
                            querystr='action=revert&rev=%d' % rev, rel='nofollow'))
                if count == 0:
                    rchecked = ' checked="checked"'
                    lchecked = ''
                elif count == 1:
                    lchecked = ' checked="checked"'
                    rchecked = ''
                else:
                    lchecked = rchecked = ''
                diff = '<input type="radio" name="rev1" value="%d"%s><input type="radio" name="rev2" value="%d"%s>' % (rev, lchecked, rev, rchecked)
                comment = line.comment
                if not comment and '/REVERT' in line.action:
                        comment = _("Revert to revision %(rev)d.") % {'rev': int(line.extra)}
            else: # ATT*
                rev = '-'
                diff = '-'

                filename = wikiutil.url_unquote(line.extra)
                comment = "%s: %s %s" % (line.action, filename, line.comment)
                size = 0
                if line.action != 'ATTDEL':
                    from MoinMoin.action import AttachFile
                    page_dir = AttachFile.getAttachDir(request, pagename)
                    filepath = os.path.join(page_dir, filename)
                    try:
                        # FIXME, wrong path on non-std names
                        size = os.path.getsize(filepath)
                    except:
                        pass
                    if line.action == 'ATTNEW':
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('view'),
                            querystr='action=AttachFile&do=view&target=%s' % filename, rel='nofollow'))
                    elif line.action == 'ATTDRW':
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('edit'),
                            querystr='action=AttachFile&drawing=%s' % filename.replace(".draw", ""), rel='nofollow'))

                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('get'),
                        querystr='action=AttachFile&do=get&target=%s' % filename, rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('del'),
                        querystr='action=AttachFile&do=del&target=%s' % filename, rel='nofollow'))
                    # XXX use?: wikiutil.escape(filename)

            history.addRow((
                rev,
                request.user.getFormattedDateTime(wikiutil.version2timestamp(line.ed_time_usecs)),
                str(size),
                diff,
                line.getEditor(request) or _("N/A"),
                wikiutil.escape(comment) or '&nbsp;',
                actions,
            ))
            count += 1
            if count >= 100:
                break

        # print version history
        from MoinMoin.widget.browser import DataBrowserWidget

        request.write('<h2>%s</h2>\n' % _('Revision History'))

        if not count: # there was no entry in logfile
            request.write(_('No log entries found.'))
            return

        # TODO: this form activates revert, which should use POST, but
        # other actions should use get. Maybe we should put the revert
        # into the page view itself, and not in this form.
        request.write('<form method="GET" action="">\n')
        request.write('<div id="page-history">\n')
        request.write('<input type="hidden" name="action" value="diff">\n')

        history_table = DataBrowserWidget(request)
        history_table.setData(history)
        history_table.render()
        request.write('</div>\n')
        request.write('</form>\n')

    # main function
    _ = request.getText
    page = Page(request, pagename)
    qpagename = wikiutil.quoteWikinameURL(pagename)
    title = page.split_title(request)

    request.emit_http_headers()

    # This action uses page or wiki language TODO: currently
    # page.language is broken and not available now, when we fix it,
    # this will be automatically fixed.
    lang = page.language or request.cfg.language_default
    request.setContentLanguage(lang)

    request.theme.send_title(_('Info for "%s"') % (title,), pagename=pagename)
    menu_items = [
        (_('Show "%(title)s"') % {'title': _('Revision History')},
         {'action': 'info'}),
        (_('Show "%(title)s"') % {'title': _('General Page Infos')},
         {'action': 'info', 'general': '1'}),
        (_('Show "%(title)s"') % {'title': _('Page hits and edits')},
         {'action': 'info', 'hitcounts': '1'}),
    ]
    request.write('<div id="content">\n') # start content div
    request.write("<p>")
    for text, querystr in menu_items:
        request.write("[%s] " % page.link_to(request, text=text, querystr=querystr, rel='nofollow'))
    request.write("</p>")

    show_hitcounts = int(request.form.get('hitcounts', [0])[0]) != 0
    show_general = int(request.form.get('general', [0])[0]) != 0

    if show_hitcounts:
        from MoinMoin.stats import hitcounts
        request.write(hitcounts.linkto(pagename, request, 'page=' + wikiutil.url_quote_plus(pagename)))
    elif show_general:
        general(page, pagename, request)
    else:
        history(page, pagename, request)

    request.write('</div>\n') # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

