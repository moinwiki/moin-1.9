# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - RecentChanges Macro

    Parameter "ddiffs" by Ralf Zosel <ralf@zosel.com>, 04.12.2003.

    @copyright: 2000-2004 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re, time
from MoinMoin import util, wikiutil, config
from MoinMoin.Page import Page
from MoinMoin.logfile import editlog

_DAYS_SELECTION = [1, 2, 3, 7, 14, 30, 60, 90]
_MAX_DAYS = 7
_MAX_PAGENAME_LENGTH = 15 # 35
_MAX_COMMENT_LENGTH = 20

#############################################################################
### RecentChanges Macro
#############################################################################

Dependencies = ["time"] # ["user", "pages", "pageparams", "bookmark"]

def format_comment(request, line):
    comment = line.comment
    _ = request.getText
    if line.action.startswith('ATT'):
        filename = wikiutil.url_unquote(line.extra)
        if line.action == 'ATTNEW':
            comment = _("Upload of attachment '%(filename)s'.") % {
                'filename': filename}
        elif line.action == 'ATTDEL':
            comment = _("Attachment '%(filename)s' deleted.") % {
                'filename': filename}
        elif line.action == 'ATTDRW':
            comment = _("Drawing '%(filename)s' saved.") % {
                'filename': filename}
    elif '/REVERT' in line.action:
        rev = int(line.extra)
        comment = _("Revert to revision %(rev)d.") % {'rev': rev}

    return wikiutil.make_breakable(comment, _MAX_COMMENT_LENGTH)

def format_page_edits(macro, lines, bookmark_usecs):
    request = macro.request
    _ = request.getText
    d = {} # dict for passing stuff to theme
    line = lines[0]
    pagename = line.pagename
    tnow = time.time()
    is_new = lines[-1].action == 'SAVENEW'
    # check whether this page is newer than the user's bookmark
    hilite = line.ed_time_usecs > (bookmark_usecs or line.ed_time_usecs)
    page = Page(request, pagename)

    html_link = ''
    if not page.exists():
        # indicate page was deleted
        html_link = request.theme.make_icon('deleted') # TODO: we could link to the last existing rev here
    elif page.isConflict():
        img = macro.formatter.smiley("/!\\")
        #img = request.theme.make_icon('help')
        html_link = page.link_to_raw(request, img, querystr={'action': 'edit'}, rel='nofollow')
    elif is_new:
        # show "NEW" icon if page was created after the user's bookmark
        if hilite:
            img = request.theme.make_icon('new')
            html_link = page.link_to_raw(request, img, rel='nofollow')
    elif hilite:
        # show "UPDATED" icon if page was edited after the user's bookmark
        img = request.theme.make_icon('updated')
        html_link = page.link_to_raw(request, img, querystr={'action': 'diff', 'date': '%d' % bookmark_usecs}, rel='nofollow')
    else:
        # show "DIFF" icon else
        img = request.theme.make_icon('diffrc')
        html_link = page.link_to_raw(request, img, querystr={'action': 'diff'}, rel='nofollow')

    # print name of page, with a link to it
    force_split = len(page.page_name) > _MAX_PAGENAME_LENGTH

    d['icon_html'] = html_link
    d['pagelink_html'] = page.link_to(request, text=page.split_title(request, force=force_split))

    # print time of change
    d['time_html'] = None
    if request.cfg.changed_time_fmt:
        tdiff = long(tnow - wikiutil.version2timestamp(long(line.ed_time_usecs))) / 60 # has to be long for py 2.2.x
        if tdiff < 100:
            d['time_html'] = _("%(mins)dm ago") % {
                'mins': tdiff}
        else:
            d['time_html'] = time.strftime(request.cfg.changed_time_fmt, line.time_tuple)

    # print editor name or IP
    d['editors'] = None
    if request.cfg.show_names:
        if len(lines) > 1:
            counters = {}
            for idx in range(len(lines)):
                name = lines[idx].getEditor(request)
                if not name in counters:
                    counters[name] = []
                counters[name].append(idx+1)
            poslist = map(None, counters.values(), counters.keys())
            poslist.sort()
            ##request.write(repr(counters.items()))
            d['editors'] = []
            for positions, name in poslist:
                d['editors'].append("%s&nbsp;[%s]" % (
                    name, util.rangelist(positions)))
        else:
            d['editors'] = [line.getEditor(request)]

    comments = []
    for idx in range(len(lines)):
        comment = format_comment(request, lines[idx])
        if comment:
            comments.append((idx+1, wikiutil.escape(comment)))

    d['changecount'] = len(lines)
    d['comments'] = comments

    img = request.theme.make_icon('info')
    d['info_html'] = page.link_to_raw(request, img, querystr={'action': 'info'}, rel='nofollow')

    return request.theme.recentchanges_entry(d)

def cmp_lines(first, second):
    return cmp(first[0], second[0])

def print_abandoned(macro, args, **kw):
    request = macro.request
    _ = request.getText
    d = {}
    pagename = macro.formatter.page.page_name
    d['q_page_name'] = wikiutil.quoteWikinameURL(pagename)
    msg = None

    pages = request.rootpage.getPageList()
    last_edits = []
    for name in pages:
        log = Page(request, name)._last_edited(request)
        if log:
            last_edits.append(log)
        #   we don't want all Systempages at the beginning of the abandoned list
        #    line = editlog.EditLogLine({})
        #    line.pagename = page
        #    line.ed_time = 0
        #    line.comment = 'not edited'
        #    line.action = ''
        #    line.userid = ''
        #    line.hostname = ''
        #    line.addr = ''
        #    last_edits.append(line)
    del pages
    last_edits.sort()

    # set max size in days
    max_days = min(int(request.form.get('max_days', [0])[0]), _DAYS_SELECTION[-1])
    # default to _MAX_DAYS for users without bookmark
    if not max_days:
        max_days = _MAX_DAYS
    d['rc_max_days'] = max_days

    # give known user the option to extend the normal display
    if request.user.valid:
        d['rc_days'] = _DAYS_SELECTION
    else:
        d['rc_days'] = None

    d['rc_update_bookmark'] = None
    request.write(request.theme.recentchanges_header(d))

    length = len(last_edits)

    index = 0
    last_index = 0
    day_count = 0

    if length > 0:
        line = last_edits[index]
        line.time_tuple = request.user.getTime(wikiutil.version2timestamp(line.ed_time_usecs))
        this_day = line.time_tuple[0:3]
        day = this_day

    while 1:

        index += 1

        if index > length:
            break

        if index < length:
            line = last_edits[index]
            line.time_tuple = request.user.getTime(wikiutil.version2timestamp(line.ed_time_usecs))
            day = line.time_tuple[0:3]

        if (day != this_day) or (index == length):
            d['bookmark_link_html'] = None
            d['date'] = request.user.getFormattedDate(wikiutil.version2timestamp(last_edits[last_index].ed_time_usecs))
            request.write(request.theme.recentchanges_daybreak(d))
            this_day = day

            for page in last_edits[last_index:index]:
                request.write(format_page_edits(macro, [page], None))
            last_index = index
            day_count += 1
            if (day_count >= max_days):
                break

    d['rc_msg'] = msg
    request.write(request.theme.recentchanges_footer(d))

def execute(macro, args, **kw):
    # handle abandoned keyword
    if kw.get('abandoned', 0):
        print_abandoned(macro, args, **kw)
        return ''

    request = macro.request
    _ = request.getText
    user = request.user
    page = macro.formatter.page
    pagename = page.page_name

    d = {}
    d['q_page_name'] = wikiutil.quoteWikinameURL(pagename)

    log = editlog.EditLog(request)

    tnow = time.time()
    msg = ""

    # get bookmark from valid user
    bookmark_usecs = request.user.getBookmark() or 0

    # add bookmark link if valid user
    d['rc_curr_bookmark'] = None
    d['rc_update_bookmark'] = None
    if request.user.valid:
        d['rc_curr_bookmark'] = _('(no bookmark set)')
        if bookmark_usecs:
            currentBookmark = wikiutil.version2timestamp(bookmark_usecs)
            currentBookmark = user.getFormattedDateTime(currentBookmark)
            currentBookmark = _('(currently set to %s)') % currentBookmark
            deleteBookmark = page.link_to(request, _("Delete bookmark"), querystr={'action': 'bookmark', 'time': 'del'}, rel='nofollow')
            d['rc_curr_bookmark'] = currentBookmark + ' ' + deleteBookmark

        version = wikiutil.timestamp2version(tnow)
        d['rc_update_bookmark'] = page.link_to(request, _("Set bookmark"), querystr={'action': 'bookmark', 'time': '%d' % version}, rel='nofollow')

    # set max size in days
    max_days = min(int(request.form.get('max_days', [0])[0]), _DAYS_SELECTION[-1])
    # default to _MAX_DAYS for useres without bookmark
    if not max_days and not bookmark_usecs:
        max_days = _MAX_DAYS
    d['rc_max_days'] = max_days

    # give known user the option to extend the normal display
    if request.user.valid:
        d['rc_days'] = _DAYS_SELECTION
    else:
        d['rc_days'] = []

    request.write(request.theme.recentchanges_header(d))

    pages = {}
    ignore_pages = {}

    today = request.user.getTime(tnow)[0:3]
    this_day = today
    day_count = 0

    for line in log.reverse():

        if not request.user.may.read(line.pagename):
            continue

        line.time_tuple = request.user.getTime(wikiutil.version2timestamp(line.ed_time_usecs))
        day = line.time_tuple[0:3]
        hilite = line.ed_time_usecs > (bookmark_usecs or line.ed_time_usecs)

        if ((this_day != day or (not hilite and not max_days))) and len(pages) > 0:
            # new day or bookmark reached: print out stuff 
            this_day = day
            for p in pages:
                ignore_pages[p] = None
            pages = pages.values()
            pages.sort(cmp_lines)
            pages.reverse()

            if request.user.valid:
                bmtime = pages[0][0].ed_time_usecs
                d['bookmark_link_html'] = page.link_to(request, _("Set bookmark"), querystr={'action': 'bookmark', 'time': '%d' % bmtime}, rel='nofollow')
            else:
                d['bookmark_link_html'] = None
            d['date'] = request.user.getFormattedDate(wikiutil.version2timestamp(pages[0][0].ed_time_usecs))
            request.write(request.theme.recentchanges_daybreak(d))

            for p in pages:
                request.write(format_page_edits(macro, p, bookmark_usecs))
            pages = {}
            day_count += 1
            if max_days and (day_count >= max_days):
                break

        elif this_day != day:
            # new day but no changes
            this_day = day

        if line.pagename in ignore_pages:
            continue

        # end listing by default if user has a bookmark and we reached it
        if not max_days and not hilite:
            msg = _('[Bookmark reached]')
            break

        if line.pagename in pages:
            pages[line.pagename].append(line)
        else:
            pages[line.pagename] = [line]
    else:
        if len(pages) > 0:
            # end of loop reached: print out stuff 
            # XXX duplicated code from above
            # but above does not trigger if we have the first day in wiki history
            for p in pages:
                ignore_pages[p] = None
            pages = pages.values()
            pages.sort(cmp_lines)
            pages.reverse()

            if request.user.valid:
                bmtime = pages[0][0].ed_time_usecs
                d['bookmark_link_html'] = page.link_to(request, _("Set bookmark"), querystr={'action': 'bookmark', 'time': '%d' % bmtime}, rel='nofollow')
            else:
                d['bookmark_link_html'] = None
            d['date'] = request.user.getFormattedDate(wikiutil.version2timestamp(pages[0][0].ed_time_usecs))
            request.write(request.theme.recentchanges_daybreak(d))

            for p in pages:
                request.write(format_page_edits(macro, p, bookmark_usecs))


    d['rc_msg'] = msg
    request.write(request.theme.recentchanges_footer(d))

    return ''


