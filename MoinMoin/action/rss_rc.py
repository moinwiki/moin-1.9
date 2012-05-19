"""
    RSS Handling

    If you do changes, please check if it still validates after your changes:

    http://feedvalidator.org/

    @copyright: 2006-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import StringIO, re, time
from MoinMoin import wikixml, config, wikiutil
from MoinMoin.logfile import editlog
from MoinMoin.util import timefuncs
from MoinMoin.Page import Page
from MoinMoin.wikixml.util import RssGenerator
from MoinMoin.action import AttachFile

def full_url(request, page, querystr=None, anchor=None):
    url = page.url(request, anchor=anchor, querystr=querystr)
    return request.getQualifiedURL(url)

def attach_url(request, pagename, filename, do):
    url = AttachFile.getAttachUrl(pagename, filename, request, do=do)
    return request.getQualifiedURL(url)

def match_page(pagename, page_pattern):
    # Match everything for empty pattern
    if not page_pattern:
        return True
    # If pattern begins with circumflex, interpret it as regex
    elif page_pattern[0] == "^":
        return re.match(page_pattern, pagename) is not None
    # Handy hack for getting rss for page tree
    elif page_pattern.endswith("/"):
        return (pagename == page_pattern[:-1]) or \
            pagename.startswith(page_pattern)
    else:
        return pagename == page_pattern

def execute(pagename, request):
    """ Send recent changes as an RSS document
    """
    if not wikixml.ok:
        request.mimetype = 'text/plain'
        request.write("rss_rc action is not supported because of missing pyxml module.")
        return

    cfg = request.cfg
    _ = request.getText

    # get params
    def_max_items = max_items = cfg.rss_items_default
    items_limit = cfg.rss_items_limit
    unique = cfg.rss_unique
    diffs = cfg.rss_diffs
    ddiffs = cfg.rss_ddiffs
    max_lines = cfg.rss_lines_default
    lines_limit = cfg.rss_lines_limit
    show_att = cfg.rss_show_attachment_entries
    page_pattern = cfg.rss_page_filter_pattern

    try:
        max_items = min(int(request.values.get('items', max_items)),
                        items_limit)
    except ValueError:
        pass
    try:
        unique = int(request.values.get('unique', unique))
    except ValueError:
        pass
    try:
        diffs = int(request.values.get('diffs', diffs))
    except ValueError:
        pass
    ## ddiffs inserted by Ralf Zosel <ralf@zosel.com>, 04.12.2003
    try:
        ddiffs = int(request.values.get('ddiffs', ddiffs))
    except ValueError:
        pass
    try:
        max_lines = min(int(request.values.get('lines', max_lines)),
                        lines_limit)
    except ValueError:
        pass
    try:
        show_att = int(request.values.get('show_att', show_att))
    except ValueError:
        pass
    try:
        page_pattern = request.values.get('page', page_pattern)
    except ValueError:
        pass

    # get data
    log = editlog.EditLog(request)
    logdata = []
    counter = 0
    pages = {}
    lastmod = 0
    for line in log.reverse():
        if not request.user.may.read(line.pagename):
            continue
        if ((not show_att and not line.action.startswith('SAVE')) or
            ((line.pagename in pages) and unique) or
            not match_page(line.pagename, page_pattern)):
            continue
        line.editor = line.getInterwikiEditorData(request)
        line.time = timefuncs.tmtuple(wikiutil.version2timestamp(line.ed_time_usecs)) # UTC
        logdata.append(line)
        pages[line.pagename] = None

        if not lastmod:
            lastmod = wikiutil.version2timestamp(line.ed_time_usecs)

        counter += 1
        if counter >= max_items:
            break
    del log

    timestamp = timefuncs.formathttpdate(lastmod)
    etag = "%d-%d-%d-%d-%d-%d-%d" % (lastmod, max_items, diffs, ddiffs, unique,
        max_lines, show_att)

    # for 304, we look at if-modified-since and if-none-match headers,
    # one of them must match and the other is either not there or must match.
    if request.if_modified_since == timestamp:
        if request.if_none_match:
            if request.if_none_match == etag:
                request.status_code = 304
        else:
            request.status_code = 304
    elif request.if_none_match == etag:
        if request.if_modified_since:
            if request.if_modified_since == timestamp:
                request.status_code = 304
        else:
            request.status_code = 304
    else:
        # generate an Expires header, using whatever setting the admin
        # defined for suggested cache lifetime of the RecentChanges RSS doc
        expires = time.time() + cfg.rss_cache

        request.mimetype = 'application/rss+xml'
        request.expires = expires
        request.last_modified = lastmod
        request.headers['Etag'] = etag

        # send the generated XML document
        baseurl = request.url_root

        logo = re.search(r'src="([^"]*)"', cfg.logo_string)
        if logo:
            logo = request.getQualifiedURL(logo.group(1))

        # prepare output
        out = StringIO.StringIO()
        handler = RssGenerator(out)

        # start SAX stream
        handler.startDocument()
        handler._out.write(unicode(
            '<!--\n'
            '    Add an "items=nnn" URL parameter to get more than the \n'
            '    default %(def_max_items)d items. You cannot get more than \n'
            '    %(items_limit)d items though.\n'
            '    \n'
            '    Add "unique=1" to get a list of changes where page names are unique,\n'
            '    i.e. where only the latest change of each page is reflected.\n'
            '    \n'
            '    Add "diffs=1" to add change diffs to the description of each items.\n'
            '    \n'
            '    Add "ddiffs=1" to link directly to the diff (good for FeedReader).\n'
            '    \n'
            '    Add "lines=nnn" to change maximum number of diff/body lines \n'
            '    to show. Cannot be more than %(lines_limit)d.\n'
            '    \n'
            '    Add "show_att=1" to show items related to attachments.\n'
            '    \n'
            '    Add "page=pattern" to show feed only for specific pages.\n'
            '    Pattern can be empty (it would match to all pages), \n'
            '    can start with circumflex (it would be interpreted as \n'
            '    regular expression in this case), end with slash (for \n'
            '    getting feed for page tree) or point to specific page (if \n'
            '    none of the above can be applied).\n'
            '    \n'
            '    Current settings: items=%(max_items)i, unique=%(unique)i, \n'
            '    diffs=%(diffs)i, ddiffs=%(ddiffs)i, lines=%(max_lines)i, \n'
            '    show_att=%(show_att)i\n'
            '-->\n' % locals()
            ).encode(config.charset))

        # emit channel description
        handler.startNode('channel', {
            (handler.xmlns['rdf'], 'about'): request.url_root,
            })
        handler.simpleNode('title', cfg.sitename)
        page = Page(request, pagename)
        handler.simpleNode('link', full_url(request, page))
        handler.simpleNode('description', u'RecentChanges at %s' % cfg.sitename)
        if logo:
            handler.simpleNode('image', None, {
                (handler.xmlns['rdf'], 'resource'): logo,
                })
        if cfg.interwikiname:
            handler.simpleNode(('wiki', 'interwiki'), cfg.interwikiname)

        handler.startNode('items')
        handler.startNode(('rdf', 'Seq'))
        for item in logdata:
            anchor = "%04d%02d%02d%02d%02d%02d" % item.time[:6]
            page = Page(request, item.pagename)
            link = full_url(request, page, anchor=anchor)
            handler.simpleNode(('rdf', 'li'), None, attr={(handler.xmlns['rdf'], 'resource'): link, })
        handler.endNode(('rdf', 'Seq'))
        handler.endNode('items')
        handler.endNode('channel')

        # emit logo data
        if logo:
            handler.startNode('image', attr={
                (handler.xmlns['rdf'], 'about'): logo,
                })
            handler.simpleNode('title', cfg.sitename)
            handler.simpleNode('link', baseurl)
            handler.simpleNode('url', logo)
            handler.endNode('image')

        # Mapping { oldname: curname } for maintaining page renames
        pagename_map = {}

        # emit items
        for item in logdata:
            if item.pagename in pagename_map:
                cur_pagename = pagename_map[item.pagename]
            else:
                cur_pagename = item.pagename
            page = Page(request, cur_pagename)
            action = item.action
            comment = item.comment
            anchor = "%04d%02d%02d%02d%02d%02d" % item.time[:6]
            rdflink = full_url(request, page, anchor=anchor)
            handler.startNode('item', attr={(handler.xmlns['rdf'], 'about'): rdflink, })

            # general attributes
            handler.simpleNode('title', item.pagename)
            handler.simpleNode(('dc', 'date'), timefuncs.W3CDate(item.time))

            show_diff = diffs

            if action.startswith('ATT'): # Attachment
                show_diff = 0
                filename = wikiutil.url_unquote(item.extra)
                att_exists = AttachFile.exists(request, cur_pagename, filename)

                if action == 'ATTNEW':
                    # Once attachment deleted this link becomes invalid but we
                    # preserve it to prevent appearance of new RSS entries in
                    # RSS readers.
                    if ddiffs:
                        handler.simpleNode('link', attach_url(request,
                            cur_pagename, filename, do='view'))

                    comment = _(u"Upload of attachment '%(filename)s'.") % {
                        'filename': filename}

                elif action == 'ATTDEL':
                    if ddiffs:
                        handler.simpleNode('link', full_url(request, page,
                            querystr={'action': 'AttachFile'}))

                    comment = _(u"Attachment '%(filename)s' deleted.") % {
                        'filename': filename}

                elif action == 'ATTDRW':
                    if ddiffs:
                        handler.simpleNode('link', attach_url(request,
                            cur_pagename, filename, do='view'))

                    comment = _(u"Drawing '%(filename)s' saved.") % {
                        'filename': filename}

            elif action.startswith('SAVE'):
                if action == 'SAVE/REVERT':
                    to_rev = int(item.extra)
                    comment = (_(u"Revert to revision %(rev)d.") % {
                        'rev': to_rev}) + "<br />" \
                        + _("Comment:") + " " + comment

                elif action == 'SAVE/RENAME':
                    show_diff = 0
                    comment = (_(u"Renamed from '%(oldpagename)s'.") % {
                        'oldpagename': item.extra}) + "<br />" \
                        + _("Comment:") + " " + comment
                    if item.pagename in pagename_map:
                        newpage = pagename_map[item.pagename]
                        del pagename_map[item.pagename]
                        pagename_map[item.extra] = newpage
                    else:
                        pagename_map[item.extra] = item.pagename

                elif action == 'SAVENEW':
                    comment = _(u"New page:\n") + comment

                item_rev = int(item.rev)

                # If we use diffs/ddiffs, we should calculate proper links and
                # content
                if ddiffs:
                    # first revision can't have older revisions to diff with
                    if item_rev == 1:
                        handler.simpleNode('link', full_url(request, page,
                            querystr={'action': 'recall',
                                      'rev': str(item_rev)}))
                    else:
                        handler.simpleNode('link', full_url(request, page,
                            querystr={'action': 'diff',
                                      'rev1': str(item_rev),
                                      'rev2': str(item_rev - 1)}))

                if show_diff:
                    if item_rev == 1:
                        lines = Page(request, cur_pagename,
                            rev=item_rev).getlines()
                    else:
                        lines = wikiutil.pagediff(request, cur_pagename,
                            item_rev - 1, cur_pagename, item_rev, ignorews=1)

                    if len(lines) > max_lines:
                        lines = lines[:max_lines] + ['...\n']

                    lines = '\n'.join(lines)
                    lines = wikiutil.escape(lines)

                    comment = u'%s\n<pre>\n%s\n</pre>\n' % (comment, lines)

                if not ddiffs:
                    handler.simpleNode('link', full_url(request, page))

            if comment:
                handler.simpleNode('description', comment)

            # contributor
            if cfg.show_names:
                edattr = {}
                if cfg.show_hosts:
                    edattr[(handler.xmlns['wiki'], 'host')] = item.hostname
                if item.editor[0] == 'interwiki':
                    edname = "%s:%s" % item.editor[1]
                    ##edattr[(None, 'link')] = baseurl + wikiutil.quoteWikiname(edname)
                else: # 'ip'
                    edname = item.editor[1]
                    ##edattr[(None, 'link')] = link + "?action=info"

                # this edattr stuff, esp. None as first tuple element breaks things (tracebacks)
                # if you know how to do this right, please send us a patch

                handler.startNode(('dc', 'contributor'))
                handler.startNode(('rdf', 'Description'), attr=edattr)
                handler.simpleNode(('rdf', 'value'), edname)
                handler.endNode(('rdf', 'Description'))
                handler.endNode(('dc', 'contributor'))

            # wiki extensions
            handler.simpleNode(('wiki', 'version'), "%i" % (item.ed_time_usecs))
            handler.simpleNode(('wiki', 'status'), ('deleted', 'updated')[page.exists()])
            handler.simpleNode(('wiki', 'diff'), full_url(request, page, querystr={'action': 'diff'}))
            handler.simpleNode(('wiki', 'history'), full_url(request, page, querystr={'action': 'info'}))
            # handler.simpleNode(('wiki', 'importance'), ) # ( major | minor )
            # handler.simpleNode(('wiki', 'version'), ) # ( #PCDATA )

            handler.endNode('item')

        # end SAX stream
        handler.endDocument()

        request.write(out.getvalue())

