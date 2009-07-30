# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - info action

    Displays page history, some general page infos and statistics.

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config, wikiutil, action
from MoinMoin.Page import Page
from MoinMoin.logfile import editlog
from MoinMoin.widget import html

def execute(pagename, request):
    """ show misc. infos about a page """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page()
        return

    def general(page, pagename, request):
        _ = request.getText
        f = request.formatter

        request.write(f.heading(1, 1),
                      f.text(_('General Information')),
                      f.heading(0, 1))

        request.write(f.paragraph(1),
                      f.text(_("Page size: %d") % page.size()),
                      f.paragraph(0))

        from MoinMoin.support.python_compatibility import hash_new
        digest = hash_new('sha1', page.get_raw_body().encode(config.charset)).hexdigest().upper()
        request.write(f.paragraph(1),
                      f.rawHTML('%(label)s <tt>%(value)s</tt>' % {
                          'label': _("SHA digest of this page's content is:"),
                          'value': digest, }),
                      f.paragraph(0))

        # show attachments (if allowed)
        attachment_info = action.getHandler(request, 'AttachFile', 'info')
        if attachment_info:
            request.write(attachment_info(pagename, request))

        # show subscribers
        subscribers = page.getSubscribers(request, include_self=1, return_users=1)
        if subscribers:
            request.write(f.paragraph(1))
            request.write(f.text(_('The following users subscribed to this page:')))
            for lang in subscribers:
                request.write(f.linebreak(), f.text('[%s] ' % lang))
                for user in subscribers[lang]:
                    # do NOT disclose email addr, only WikiName
                    userhomepage = Page(request, user.name)
                    if userhomepage.exists():
                        request.write(f.rawHTML(userhomepage.link_to(request) + ' '))
                    else:
                        request.write(f.text(user.name + ' '))
            request.write(f.paragraph(0))

        # show links
        links = page.getPageLinks(request)
        if links:
            request.write(f.paragraph(1))
            request.write(f.text(_('This page links to the following pages:')))
            request.write(f.linebreak())
            for linkedpage in links:
                request.write(f.rawHTML("%s%s " % (Page(request, linkedpage).link_to(request), ",."[linkedpage == links[-1]])))
            request.write(f.paragraph(0))

    def history(page, pagename, request):
        # show history as default
        _ = request.getText
        default_count, limit_max_count = request.cfg.history_count
        try:
            max_count = int(request.form.get('max_count', [default_count])[0])
        except:
            max_count = default_count
        max_count = min(max_count, limit_max_count)

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

        def render_action(text, query, **kw):
            kw.update(dict(rel='nofollow'))
            return page.link_to(request, text, querystr=query, **kw)

        # read in the complete log of this page
        log = editlog.EditLog(request, rootpagename=pagename)
        count = 0
        pgactioncount = 0
        for line in log.reverse():
            rev = int(line.rev)
            actions = []
            if line.action in ('SAVE', 'SAVENEW', 'SAVE/REVERT', 'SAVE/RENAME', ):
                size = page.size(rev=rev)
                actions.append(render_action(_('view'), {'action': 'recall', 'rev': '%d' % rev}))
                if pgactioncount == 0:
                    rchecked = ' checked="checked"'
                    lchecked = ''
                elif pgactioncount == 1:
                    lchecked = ' checked="checked"'
                    rchecked = ''
                else:
                    lchecked = rchecked = ''
                diff = '<input type="radio" name="rev1" value="%d"%s><input type="radio" name="rev2" value="%d"%s>' % (rev, lchecked, rev, rchecked)
                if rev > 1:
                    diff += render_action(' ' + _('to previous'), {'action': 'diff', 'rev1': rev-1, 'rev2': rev})
                comment = line.comment
                if not comment:
                    if '/REVERT' in line.action:
                        comment = _("Revert to revision %(rev)d.") % {'rev': int(line.extra)}
                    elif '/RENAME' in line.action:
                        comment = _("Renamed from '%(oldpagename)s'.") % {'oldpagename': line.extra}
                pgactioncount += 1
            else: # ATT*
                rev = '-'
                diff = '-'

                filename = wikiutil.url_unquote(line.extra)
                comment = "%s: %s %s" % (line.action, filename, line.comment)
                size = 0
                if line.action != 'ATTDEL':
                    from MoinMoin.action import AttachFile
                    if AttachFile.exists(request, pagename, filename):
                        size = AttachFile.size(request, pagename, filename)
                    if line.action == 'ATTNEW':
                        actions.append(render_action(_('view'), {'action': 'AttachFile', 'do': 'view', 'target': '%s' % filename}))
                    elif line.action == 'ATTDRW':
                        actions.append(render_action(_('edit'), {'action': 'AttachFile', 'drawing': '%s' % filename.replace(".draw", "")}))

                    actions.append(render_action(_('get'), {'action': 'AttachFile', 'do': 'get', 'target': '%s' % filename}))
                    if request.user.may.delete(pagename):
                        actions.append(render_action(_('del'), {'action': 'AttachFile', 'do': 'del', 'target': '%s' % filename}))

            history.addRow((
                rev,
                request.user.getFormattedDateTime(wikiutil.version2timestamp(line.ed_time_usecs)),
                str(size),
                diff,
                line.getEditor(request) or _("N/A"),
                wikiutil.escape(comment) or '&nbsp;',
                "&nbsp;".join(actions),
            ))
            count += 1
            if count >= max_count:
                break

        # print version history
        from MoinMoin.widget.browser import DataBrowserWidget

        request.write(unicode(html.H2().append(_('Revision History'))))

        if not count: # there was no entry in logfile
            request.write(_('No log entries found.'))
            return

        history_table = DataBrowserWidget(request)
        history_table.setData(history)

        div = html.DIV(id="page-history")
        div.append(html.INPUT(type="hidden", name="action", value="diff"))
        div.append(history_table.render(method="GET"))

        form = html.FORM(method="GET", action="")
        form.append(div)
        request.write(unicode(form))

    # main function
    _ = request.getText
    page = Page(request, pagename)
    title = page.split_title()

    request.emit_http_headers()

    request.setContentLanguage(request.lang)
    f = request.formatter

    request.theme.send_title(_('Info for "%s"') % (title, ), page=page)
    menu_items = [
        (_('Show "%(title)s"') % {'title': _('Revision History')},
         {'action': 'info'}),
        (_('Show "%(title)s"') % {'title': _('General Page Infos')},
         {'action': 'info', 'general': '1'}),
        (_('Show "%(title)s"') % {'title': _('Page hits and edits')},
         {'action': 'info', 'hitcounts': '1'}),
    ]
    request.write(f.div(1, id="content")) # start content div
    request.write(f.paragraph(1))
    for text, querystr in menu_items:
        request.write("[%s] " % page.link_to(request, text=text, querystr=querystr, rel='nofollow'))
    request.write(f.paragraph(0))

    try:
        show_hitcounts = int(request.form.get('hitcounts', [0])[0]) != 0
    except ValueError:
        show_hitcounts = False
    try:
        show_general = int(request.form.get('general', [0])[0]) != 0
    except ValueError:
        show_general = False

    if show_hitcounts:
        from MoinMoin.stats import hitcounts
        request.write(hitcounts.linkto(pagename, request, 'page=' + wikiutil.url_quote(pagename)))
    elif show_general:
        general(page, pagename, request)
    else:
        history(page, pagename, request)

    request.write(f.div(0)) # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

