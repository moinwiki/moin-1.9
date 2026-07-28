# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - info action

    Displays the page history. It used to show some general page infos and
    statistics as well, see the comment in execute() for why it does not.

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import wikiutil
from MoinMoin.Page import Page
from MoinMoin.logfile import editlog
from MoinMoin.widget import html
from MoinMoin.action import AttachFile

def execute(pagename, request):
    """ show misc. infos about a page """
    # The "Page hits and edits" and "General Page Infos" views are not served
    # any more, info only shows the revision history now. Each of them was an
    # url per page of the wiki for a crawler to find, and neither is cheap:
    # hitcounts puts a chart on the page whose image url makes us walk the
    # whole event log, and general hashes the page body and collects its
    # attachments, subscribers and outgoing links. There is nothing to show
    # instead of them, so this is a 404 rather than a redirect to the history.
    # Note we do not int() the values: whatever they say, these views are gone.
    if request.values.get('hitcounts') or request.values.get('general'):
        request.makeForbidden(404, 'this info view is gone, only the history is left')

    if not request.user.may.read(pagename):
        Page(request, pagename).send_page()
        return

    def history(page, pagename, request):
        # show history as default
        _ = request.getText
        default_count, limit_max_count = request.cfg.history_count[0:2]
        paging = request.cfg.history_paging

        try:
            max_count = int(request.values.get('max_count', default_count))
        except ValueError:
            max_count = default_count
        max_count = max(1, min(max_count, limit_max_count))

        # read in the complete log of this page
        log = editlog.EditLog(request, rootpagename=pagename)

        offset = 0
        paging_info_html = ""
        paging_nav_html = ""
        count_select_html = ""

        f = request.formatter

        if paging:
            log_size = log.lines()

            try:
                offset = int(request.values.get('offset', 0))
            except ValueError:
                offset = 0
            offset = max(min(offset, log_size - 1), 0)

            # The Newer / Older buttons say which way to move, the offset they
            # move from comes from the form they are in (see paging_nav_html
            # below). Moving is done here so that everything after this - the
            # "showing entries from ... to ..." line, the buttons and the rows
            # of the listing - sees the offset that is actually shown.
            offsetmove = request.values.get('offsetmove', u'')
            if offsetmove == u'newer':
                offset = ((offset - 1) / max_count) * max_count
            elif offsetmove == u'older':
                offset = ((offset + max_count) / max_count) * max_count
            offset = max(min(offset, log_size - 1), 0)

            paging_info_html += f.paragraph(1, css_class="searchstats info-paging-info") + _("Showing page edit history entries from '''%(start_offset)d''' to '''%(end_offset)d''' out of '''%(total_count)d''' entries total.", wiki=True) % {
                'start_offset': log_size - min(log_size, offset + max_count) + 1,
                'end_offset': log_size - offset,
                'total_count': log_size,
            } + f.paragraph(0)

            # generating offset navigation
            if max_count < log_size or offset != 0:
                # This used to be a row of links: "Newer", "Older", the first
                # and the last page of the log and the numbered pages around
                # the current one. That is an url per page of the listing, and
                # crawlers walked all of them. Two buttons reach the same
                # places, one page at a time - they only say which way to go,
                # the offset they move from is in the form around them.
                def offset_button(direction, caption, enabled):
                    return '<button type="submit" name="offsetmove" value="%s"%s>%s</button> ' % (
                        direction,
                        not enabled and ' disabled="disabled"' or '',
                        wikiutil.escape(caption))

                paging_nav_html += (
                    offset_button('newer', _("Newer"), offset > 0) +
                    offset_button('older', _("Older"), offset < (log_size - max_count)))

        # generating max_count switcher
        # we do it only in case history_count has additional values
        if len(request.cfg.history_count) > 2:
            max_count_possibilities = list(set(request.cfg.history_count))
            max_count_possibilities.sort()
            max_count_html = []
            cur_count_added = False

            for count in max_count_possibilities:
                # max count value can be not in list of predefined values
                if max_count <= count and not cur_count_added:
                    max_count_html.append('<option value="%d" selected="selected">%d</option>'
                                          % (max_count, max_count))
                    cur_count_added = True

                # checking for limit_max_count to prevent showing unavailable options
                if max_count != count and count <= limit_max_count:
                    max_count_html.append('<option value="%d">%d</option>' % (count, count))

            # This used to be one link per possible count, which gave a crawler
            # an url per (offset, count) combination. It is a select of the
            # paging form now - the same select-and-press-Do that the theme
            # uses for its actions menu - so it costs nothing until somebody
            # actually uses it. That form carries the action and the offset,
            # so this button needs no name of its own.
            count_select_html += "".join([
                f.span(1, css_class="info-count-selector"),
                    f.text(" ("),
                    f.text(_("%s items per page")) % (
                        '<select name="max_count" class="info-count-select">%s</select>'
                        % "".join(max_count_html)),
                    f.rawHTML(' <button type="submit">%s</button>' % wikiutil.escape(_("Do"))),
                    f.text(")"),
                f.span(0),
            ])

        # open log for this page
        from MoinMoin.util.dataset import TupleDataset, Column

        history = TupleDataset()
        history.columns = [
            Column('rev', label='#', align='right'),
            Column('mtime', label=_('Date'), align='right'),
            Column('size', label=_('Size'), align='right'),
            # both column headers submit the one form around the table, the
            # pressed button decides which action the form runs
            Column('diff', label='<button type="submit" name="action" value="diff">%s</button>' % (_("Diff"))),
            Column('editor', label=_('Editor'), hidden=not request.cfg.show_names),
            Column('comment', label=_('Comment')),
            Column('action', label='<button type="submit" name="action" value="info">%s</button>' % (_("Do"))),
            ]

        # generate history list

        # The actions of a row used to be links, which gave a crawler one url
        # per revision and per attachment, each of them rendering a complete
        # page. They are radio buttons of a single group now: picking one and
        # pressing the button in the column header runs it, and crawlers do not
        # submit forms. See the rowaction handling in execute() below.
        def render_action(text, value):
            return '<input type="radio" name="rowaction" value="%s">%s' % (
                wikiutil.escape(value, True), wikiutil.escape(text))

        def render_file_action(text, filename, do):
            # do not offer what this file has no handler for (as before: the
            # link was left out when getAttachUrl() had nothing to point to)
            if AttachFile.get_action(request, filename, do):
                return render_action(text, u'AttachFile:%s:%s' % (do, filename))

        may_write = request.user.may.write(pagename)
        may_delete = request.user.may.delete(pagename)

        count = 0
        pgactioncount = 0
        for line in log.reverse():
            count += 1

            if paging and count <= offset:
                continue

            rev = int(line.rev)
            actions = []
            if line.action in ('SAVE', 'SAVENEW', 'SAVE/REVERT', 'SAVE/RENAME', ):
                size = page.size(rev=rev)
                actions.append(render_action(_('view'), u'recall:%d' % rev))
                if pgactioncount == 0:
                    rchecked = ' checked="checked"'
                    lchecked = ''
                elif pgactioncount == 1:
                    lchecked = ' checked="checked"'
                    rchecked = ''
                else:
                    lchecked = rchecked = ''
                # Note: there used to be a "to previous" diff link per row here.
                # Those links were the diff urls a crawler picked up from this
                # page - one per revision, each of them rendering two revisions
                # and (for fancy diffs) the whole page below the diff. The radio
                # buttons in this same column do that and more, they compare any
                # two of the listed revisions, and being a GET form they are not
                # followed by crawlers.
                diff = '<input type="radio" name="rev1" value="%d"%s><input type="radio" name="rev2" value="%d"%s>' % (rev, lchecked, rev, rchecked)
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
                if AttachFile.exists(request, pagename, filename):
                    size = AttachFile.size(request, pagename, filename)
                    actions.append(render_file_action(_('view'), filename, 'view'))
                    actions.append(render_file_action(_('get'), filename, 'get'))
                    if may_delete:
                        actions.append(render_file_action(_('del'), filename, 'del'))
                    if may_write:
                        actions.append(render_file_action(_('edit'), filename, 'modify'))
                else:
                    size = 0

            history.addRow((
                rev,
                request.user.getFormattedDateTime(wikiutil.version2timestamp(line.ed_time_usecs)),
                str(size),
                diff,
                line.getEditor(request) or _("N/A"),
                wikiutil.escape(comment) or '&nbsp;',
                "&nbsp;".join(a for a in actions if a),
            ))
            if (count >= max_count + offset) or (paging and count >= log_size):
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
        div.append(history_table.render(method="GET"))

        # The paging controls are a form of their own, next to (not inside) the
        # one around the history table: that one can not have a fixed action,
        # its buttons each bring their own, while these all mean action=info.
        # So a hidden input can carry it here, which leaves the buttons free to
        # say what they do - pick a count, or move a page.
        def paging_form(css_class, content, hidden_max_count=False):
            return "".join([
                '<form method="GET" action="">',
                f.div(1, css_class=css_class),
                '<input type="hidden" name="action" value="info">',
                '<input type="hidden" name="offset" value="%d">' % offset,
                hidden_max_count and '<input type="hidden" name="max_count" value="%d">' % max_count or '',
                content,
                f.div(0),
                '</form>',
            ])

        if paging:
            request.write(paging_form("info-paging-info",
                                      paging_info_html + count_select_html))

        # The table brings its own form - that is what render(method="GET")
        # does - and the radio buttons and the two column header buttons are
        # inside it. There used to be another form around it here, holding the
        # hidden action=diff; now that those buttons carry their action
        # themselves, that outer form would only be a form nested in a form,
        # which is not allowed and which browsers resolve by dropping the
        # inner start tag, so that the inner </form> ends the outer one.
        request.write(unicode(div))

        if paging:
            # down here the count select is out of reach, so the count the
            # buttons move within has to be carried along
            request.write(paging_form("info-paging-nav info-paging-nav-bottom",
                                      paging_nav_html, hidden_max_count=True))

    # main function
    _ = request.getText
    page = Page(request, pagename)

    # A row action was selected in the history and the form was submitted (see
    # render_action() above): send the browser to the action it stands for.
    # The url is built here from a fixed set of actions, the submitted value
    # only selects one of them and gives its target, so this can not be used to
    # send anybody somewhere else. The actions check their own permissions, as
    # they did when these were links.
    rowaction = request.values.get('rowaction', u'')
    if rowaction:
        what = rowaction.split(u':', 2)
        url = None
        if len(what) == 2 and what[0] == u'recall' and what[1].isdigit():
            url = page.url(request, querystr={'action': 'recall', 'rev': str(int(what[1]))})
        elif len(what) == 3 and what[0] == u'AttachFile' and what[1] in ('view', 'get', 'del', 'modify'):
            # getAttachUrl() creates the ticket the destructive ones need
            url = AttachFile.getAttachUrl(pagename, what[2], request, do=what[1])
        if url:
            request.http_redirect(url)
            return

    title = page.split_title()

    request.setContentLanguage(request.lang)
    f = request.formatter

    request.theme.send_title(_('Info for "%s"') % (title, ), page=page)
    request.write(f.div(1, id="content")) # start content div
    # There used to be a menu of the three views info offered, first as links
    # (an url per view on every page of the wiki, and the history one leads on
    # to the whole page history), then as a GET form that crawlers do not
    # submit. The revision history is the only view left, so a menu to pick it
    # would only ever re-request the page it is on.
    history(page, pagename, request)

    request.write(f.div(0)) # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

