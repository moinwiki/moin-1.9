# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - show diff between 2 page revisions

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006-2008 MoinMoin:ThomasWaldmann,
                2009 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil
from MoinMoin.logfile import editlog
from MoinMoin.Page import Page

# A diff url names two revisions, so a page with n revisions has n*(n-1)/2 of
# them and serving one of them means rendering two revisions (plus the whole
# page below the diff, for fancy diffs). Crawlers ignore rel=nofollow, so
# instead of offering that many urls we only serve the diffs worth having:
# * any comparison within the most recent DIFF_RECENT_REVS revisions, and
# * comparisons spanning at most DIFF_MAX_SPAN revisions, anywhere in the
#   history.
# Neither set grows faster than linearly with the amount of revisions. A
# request for anything else is refused with a 403.
# May be overridden in the wiki config as diff_recent_revs / diff_max_span.
DIFF_RECENT_REVS = 20
DIFF_MAX_SPAN = 5

def execute(pagename, request):
    """ Handle "action=diff"
        checking for either a "rev=formerrevision" parameter
        or rev1 and rev2 parameters
    """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page()
        return

    try:
        date = request.values['date']
        try:
            date = long(date) # must be long for py 2.2.x
        except StandardError:
            date = 0
    except KeyError:
        date = 0

    try:
        rev1 = int(request.values.get('rev1', -1))
    except StandardError:
        rev1 = 0
    try:
        rev2 = int(request.values.get('rev2', 0))
    except StandardError:
        rev2 = 0

    if rev1 == -1 and rev2 == 0:
        rev1 = request.rev
        if rev1 is None:
            rev1 = -1

    # spacing flag?
    ignorews = int(request.values.get('ignorews', 0))

    _ = request.getText

    # get a list of old revisions, and back out if none are available
    currentpage = Page(request, pagename)
    currentrev = currentpage.current_rev()
    if currentrev < 2:
        request.theme.add_msg(_("No older revisions available!"), "error")
        currentpage.send_page()
        return

    if date: # this is how we get called from RecentChanges
        rev1 = 0
        log = editlog.EditLog(request, rootpagename=pagename)
        for line in log.reverse():
            if date >= line.ed_time_usecs and int(line.rev) != 99999999:
                rev1 = int(line.rev)
                break
        else:
            rev1 = 1
        rev2 = 0

    if rev1 > 0 and rev2 > 0 and rev1 > rev2 or rev1 == 0 and rev2 > 0:
        rev1, rev2 = rev2, rev1

    if rev1 == -1:
        oldrev = currentrev - 1
        oldpage = Page(request, pagename, rev=oldrev)
    elif rev1 == 0:
        oldrev = currentrev
        oldpage = currentpage
    else:
        oldrev = rev1
        oldpage = Page(request, pagename, rev=oldrev)

    if rev2 == 0:
        newrev = currentrev
        newpage = currentpage
    else:
        newrev = rev2
        newpage = Page(request, pagename, rev=newrev)

    # which revisions we compare is controlled by whoever requests the page,
    # so refuse the ones we do not offer a way to reach (see above) before
    # doing any work for them.
    recent_revs = getattr(request.cfg, 'diff_recent_revs', DIFF_RECENT_REVS)
    max_span = getattr(request.cfg, 'diff_max_span', DIFF_MAX_SPAN)
    oldest_recent_rev = currentrev - recent_revs + 1
    if ((oldrev < oldest_recent_rev or newrev < oldest_recent_rev) and
        abs(newrev - oldrev) > max_span):
        request.makeForbidden(403, 'diff: revisions too old and too far apart')

    oldlog = oldpage.editlog_entry()
    newlog = newpage.editlog_entry()

    if not oldlog or not newlog:
        # We use "No log entries found." msg because we already have i18n
        # for that. Better would "At least one log entry was not found.".
        request.theme.add_msg(_("No log entries found."), "error")
        currentpage.send_page()
        return

    edit_count = abs(newrev - oldrev)

    # Start output
    # This action generates content in the user language
    request.setContentLanguage(request.lang)

    request.theme.send_title(_('Diff for "%s"') % (pagename, ), pagename=pagename, allow_doubleclick=1)

    f = request.formatter
    request.write(f.div(1, id="content"))

    oldrev = oldpage.get_real_rev()
    newrev = newpage.get_real_rev()

    title = _('Differences between revisions %d and %d') % (oldrev, newrev)
    if edit_count > 1:
        title += ' ' + _('(spanning %d versions)') % (edit_count, )
    title = f.text(title)

    page_url = wikiutil.escape(currentpage.url(request), True)

    def enabled(val):
        return not val and u' disabled="disabled"' or u''

    revert_html = ""
    if request.user.may.revert(pagename):
        revert_html = """
  <form action="%s" method="get">
   <div style="text-align:center">
    <input name="action" value="revert" type="hidden">
    <input name="rev" value="%d" type="hidden">
    <input value="%s" type="submit"%s>
   </div>
  </form>
 """ % (page_url, rev2, _("Revert to this revision"), enabled(newrev < currentrev))

    other_diff_button_html = """
 <td style="border:0;">
  <form action="%s" method="get">
   <div style="text-align:%s">
    <input name="action" value="diff" type="hidden">
    <input name="rev1" value="%d" type="hidden">
    <input name="rev2" value="%d" type="hidden">
    <input value="%s" type="submit"%s>
   </div>
  </form>
 </td>
"""

    navigation_html = """
<span class="diff-header">%%s</span>
<table class="diff">
<tr>
 %(button)s
 <td style="border:0">
   %%s
 </td>
 %(button)s
</tr>
</table>
""" % {'button': other_diff_button_html}

    prev_oldrev = (oldrev > 1) and (oldrev - 1) or 1
    next_newrev = (newrev < currentrev) and (newrev + 1) or currentrev

    navigation_html = navigation_html % (title,
       page_url, "left", prev_oldrev, oldrev, _("Previous change"), enabled(oldrev > 1),
       revert_html,
       page_url, "right", newrev, next_newrev, _("Next change"), enabled(newrev < currentrev), )

    request.write(f.rawHTML(navigation_html))

    # Note: there used to be a per-pane navigation of <= < > >= links here,
    # moving rev1 and rev2 independently. As both sides could be moved on
    # their own, following those links reached every (rev1, rev2) combination,
    # which is rev_count*(rev_count-1)/2 distinct urls for a single page - and
    # each of them renders two revisions plus (for fancy diffs) the whole page
    # below the diff. Crawlers ignore rel=nofollow and walked all of them.
    # The same diffs are still available without offering that many urls:
    # the "Previous change" / "Next change" buttons above step through the
    # revisions, and the info action has a radio button per revision to
    # compare any two of them. Both are GET forms, so they cost us nothing
    # unless somebody actually clicks.

    rev_info_html = """
  <div class="diff-info diff-info-header">%(rev_header)s</div>
  <div class="diff-info diff-info-rev-size"><span class="diff-info-caption">%(rev_size_caption)s:</span> <span class="diff-info-value">%%(rev_size)d</span></div>
  <div class="diff-info diff-info-rev-author"><span class="diff-info-caption">%(rev_author_caption)s:</span> <span class="diff-info-value">%%(rev_author)s</span></div>
  <div class="diff-info diff-info-rev-comment"><span class="diff-info-caption">%(rev_comment_caption)s:</span> <span class="diff-info-value">%%(rev_comment)s</span></div>
""" % {
    'rev_header': _('Revision %(rev)d as of %(date)s'),
    'rev_size_caption': _('Size'),
    'rev_author_caption': _('Editor'),
    'rev_ts_caption': _('Date'),
    'rev_comment_caption': _('Comment'),
}

    rev_info_old_html = rev_info_html % {
        'rev': oldrev,
        'rev_size': oldpage.size(),
        'rev_author': oldlog.getEditor(request) or _('N/A'),
        'date': request.user.getFormattedDateTime(wikiutil.version2timestamp(oldlog.ed_time_usecs)) or _('N/A'),
        'rev_comment': wikiutil.escape(oldlog.comment) or '',
    }

    rev_info_new_html = rev_info_html % {
        'rev': newrev,
        'rev_size': newpage.size(),
        'rev_author': newlog.getEditor(request) or _('N/A'),
        'date': request.user.getFormattedDateTime(wikiutil.version2timestamp(newlog.ed_time_usecs)) or _('N/A'),
        'rev_comment': wikiutil.escape(newlog.comment) or '',
    }

    if request.user.show_fancy_diff:
        from MoinMoin.util import diff_html
        request.write(f.rawHTML(diff_html.diff(request, oldpage.get_raw_body(), newpage.get_raw_body(), old_top=rev_info_old_html, new_top=rev_info_new_html, old_top_class="diff-info", new_top_class="diff-info")))
        newpage.send_page(count_hit=0, content_only=1, content_id="content-below-diff")
    else:
        request.write(f.rawHTML('<table class="diff"><tr><td class="diff-info">%s</td><td class="diff-info">%s</td></tr></table>' % (rev_info_old_html, rev_info_new_html)))

        from MoinMoin.util import diff_text
        lines = diff_text.diff(oldpage.getlines(), newpage.getlines())
        if not lines:
            msg = f.text(" - " + _("No differences found!"))
            if edit_count > 1:
                msg = msg + f.paragraph(1) + f.text(_('The page was saved %(count)d times, though!') % {
                    'count': edit_count}) + f.paragraph(0)
            request.write(msg)
        else:
            if ignorews:
                request.write(f.text(_('(ignoring whitespace)')), f.linebreak())
            else:
                qstr = {'action': 'diff', 'ignorews': '1', }
                if rev1:
                    qstr['rev1'] = str(rev1)
                if rev2:
                    qstr['rev2'] = str(rev2)
                request.write(f.paragraph(1), Page(request, pagename).link_to(request,
                    text=_('Ignore changes in the amount of whitespace'),
                    querystr=qstr, rel='nofollow'), f.paragraph(0))

            request.write(f.preformatted(1))
            for line in lines:
                if line[0] == "@":
                    request.write(f.rule(1))
                request.write(f.text(line + '\n'))
            request.write(f.preformatted(0))

    request.write(f.div(0)) # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

