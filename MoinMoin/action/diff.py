# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - show diff between 2 page revisions

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 by MoinMoin:ThomasWaldmann
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
        Page(request, pagename).send_page(request)
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
        rev1 = 0

    if rev1 == -1 and rev2 == 0:
        try:
            rev1 = int(request.form.get('rev', [-1])[0])
        except StandardError:
            rev1 = -1

    # spacing flag?
    ignorews = int(request.form.get('ignorews', [0])[0])

    _ = request.getText

    # get a list of old revisions, and back out if none are available
    currentpage = Page(request, pagename)
    revisions = currentpage.getRevList()
    if len(revisions) < 2:
        currentpage.send_page(request, msg=_("No older revisions available!"))
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
    # This action generate content in the user language
    request.setContentLanguage(request.lang)

    request.emit_http_headers()
    request.theme.send_title(_('Diff for "%s"') % (pagename,), pagename=pagename, allow_doubleclick=1)

    if rev1 > 0 and rev2 > 0 and rev1 > rev2 or rev1 == 0 and rev2 > 0:
        rev1, rev2 = rev2, rev1

    oldrev1, oldcount1 = None, 0
    oldrev2, oldcount2 = None, 0

    # get the filename of the version to compare to
    edit_count = 0
    for rev in revisions:
        edit_count += 1
        if rev <= rev1:
            oldrev1, oldcount1 = rev, edit_count
        if rev2 and rev >= rev2:
            oldrev2, oldcount2 = rev, edit_count
        if oldrev1 and oldrev2 or oldrev1 and not rev2:
            break

    if rev1 == -1:
        oldpage = Page(request, pagename, rev=revisions[1])
        oldcount1 -= 1
    elif rev1 == 0:
        oldpage = currentpage
        # oldcount1 is still on init value 0
    else:
        if oldrev1:
            oldpage = Page(request, pagename, rev=oldrev1)
        else:
            oldpage = Page(request, "$EmptyPage$") # hack
            oldpage.set_raw_body("")    # avoid loading from disk
            oldrev1 = 0 # XXX

    if rev2 == 0:
        newpage = currentpage
        # oldcount2 is still on init value 0
    else:
        if oldrev2:
            newpage = Page(request, pagename, rev=oldrev2)
        else:
            newpage = Page(request, "$EmptyPage$") # hack
            newpage.set_raw_body("")    # avoid loading from disk
            oldrev2 = 0 # XXX

    edit_count = abs(oldcount1 - oldcount2)

    # this should use the formatter, but there is none?
    request.write('<div id="content">\n') # start content div
    request.write('<p class="diff-header">')
    request.write(_('Differences between revisions %d and %d') % (oldpage.get_real_rev(), newpage.get_real_rev()))
    if edit_count > 1:
        request.write(' ' + _('(spanning %d versions)') % (edit_count,))
    request.write('</p>')

    if request.user.show_fancy_diff:
        from MoinMoin.util import diff_html
        request.write(diff_html.diff(request, oldpage.get_raw_body(), newpage.get_raw_body()))
        newpage.send_page(request, count_hit=0, content_only=1, content_id="content-below-diff")
    else:
        from MoinMoin.util import diff_text
        lines = diff_text.diff(oldpage.getlines(), newpage.getlines())
        if not lines:
            msg = _("No differences found!")
            if edit_count > 1:
                msg = msg + '<p>' + _('The page was saved %(count)d times, though!') % {
                    'count': edit_count}
            request.write(msg)
        else:
            if ignorews:
                request.write(_('(ignoring whitespace)') + '<br>')
            else:
                qstr = {'action': 'diff', 'ignorews': '1', }
                if rev1:
                    qstr['rev1'] = str(rev1)
                if rev2:
                    qstr['rev2'] = str(rev2)
                request.write(Page(request, pagename).link_to(request,
                    text=_('Ignore changes in the amount of whitespace'),
                    querystr=qstr, rel='nofollow') + '<p>')

            request.write('<pre>')
            for line in lines:
                if line[0] == "@":
                    request.write('<hr>')
                request.write(wikiutil.escape(line)+'\n')
            request.write('</pre>')

    request.write('</div>\n') # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

