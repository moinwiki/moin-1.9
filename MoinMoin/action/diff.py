# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - show diff between 2 page revisions

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006-2008 MoinMoin:ThomasWaldmann,
                2009 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.logfile import editlog
from MoinMoin.Page import Page

def execute(pagename, request):
    """ Handle "action=diff"
        checking for either a "rev=formerrevision" parameter
        or rev1 and rev2 parameters
    """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page()
        return

    try:
        date = request.form['date'][0]
        try:
            date = long(date) # must be long for py 2.2.x
        except StandardError:
            date = 0
    except KeyError:
        date = 0

    try:
        rev1 = int(request.form.get('rev1', [-1])[0])
    except StandardError:
        rev1 = 0
    try:
        rev2 = int(request.form.get('rev2', [0])[0])
    except StandardError:
        rev2 = 0

    if rev1 == -1 and rev2 == 0:
        rev1 = request.rev
        if rev1 is None:
            rev1 = -1

    # spacing flag?
    ignorews = int(request.form.get('ignorews', [0])[0])

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

    # Start output
    # This action generates content in the user language
    request.setContentLanguage(request.lang)

    request.emit_http_headers()
    request.theme.send_title(_('Diff for "%s"') % (pagename, ), pagename=pagename, allow_doubleclick=1)

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

    edit_count = abs(newrev - oldrev)

    f = request.formatter
    request.write(f.div(1, id="content"))

    oldrev = oldpage.get_real_rev()
    newrev = newpage.get_real_rev()

    revlist = currentpage.getRevList()

    # code below assumes that the page exists and has at least
    # one revision in the revlist, just bail out if not. Users
    # shouldn't really run into this anyway.
    if not revlist:
        request.write(f.div(0)) # end content div
        request.theme.send_footer(pagename)
        request.theme.send_closing_html()
        return

    title = _('Differences between revisions %d and %d') % (oldrev, newrev)
    if edit_count > 1:
        title += ' ' + _('(spanning %d versions)') % (edit_count, )
    title = f.text(title)

    # Revision list starts from 2...
    if oldrev <= min(revlist):
        disable_prev = u' disabled="disabled"'
    else:
        disable_prev = u''

    if newrev >= max(revlist):
        disable_next = u' disabled="disabled"'
    else:
        disable_next = u''

    page_url = wikiutil.escape(currentpage.url(request), True)

    revert_html = ""
    if request.user.may.revert(pagename):
        revert_html = """
 <td style="border:0">
  <form action="%s" method="get">
   <div style="text-align:center">
    <input name="action" value="revert" type="hidden">
    <input name="rev" value="%d" type="hidden">
    <input value="%s" type="submit"%s>
   </div>
  </form>
 </td>
 """ % (page_url, rev2, _("Revert to this revision"), disable_next)

    navigation_html = """
<span class="diff-header">%s</span>
<table class="diff">
<tr>
 <td style="border:0">
  <form action="%s" method="get">
   <div style="text-align:left">
    <input name="action" value="diff" type="hidden">
    <input name="rev1" value="%d" type="hidden">
    <input name="rev2" value="%d" type="hidden">
    <input value="%s" type="submit"%s>
   </div>
  </form>
 </td>
 %s
 <td style="border:0">
  <form action="%s" method="get">
   <div style="text-align:right">
    <input name="action" value="diff" type="hidden">
    <input name="rev1" value="%d" type="hidden">
    <input name="rev2" value="%d" type="hidden">
    <input value="%s" type="submit"%s>
   </div>
  </form>
 </td>
</tr>
</table>
""" % (title,
       page_url, oldrev - 1, oldrev, _("Previous change"), disable_prev,
       revert_html,
       page_url, newrev, newrev + 1, _("Next change"), disable_next, )

    request.write(f.rawHTML(navigation_html))

    if request.user.show_fancy_diff:
        from MoinMoin.util import diff_html
        request.write(f.rawHTML(diff_html.diff(request, oldpage.get_raw_body(), newpage.get_raw_body())))
        newpage.send_page(count_hit=0, content_only=1, content_id="content-below-diff")
    else:
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

