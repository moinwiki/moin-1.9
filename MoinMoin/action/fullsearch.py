# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - fullsearch action

    This is the backend of the search form. Search pages and print results.

    @copyright: 2001 by Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re, time
from MoinMoin.Page import Page
from MoinMoin import wikiutil
from MoinMoin.support.parsedatetime.parsedatetime import Calendar

def checkTitleSearch(request):
    """ Return 1 for title search, 0 for full text search, -1 for idiot spammer
        who tries to press all buttons at once.

    When used in FullSearch macro, we have 'titlesearch' parameter with
    '0' or '1'. In standard search, we have either 'titlesearch' or
    'fullsearch' with localized string. If both missing, default to
    True (might happen with Safari) if this isn't an advanced search.
"""
    form = request.form
    if 'titlesearch' in form and 'fullsearch' in form:
        ret = -1 # spammer / bot
    else:
        try:
            ret = int(form['titlesearch'][0])
        except ValueError:
            ret = 1
        except KeyError:
            ret = ('fullsearch' not in form and not isAdvancedSearch(request)) and 1 or 0
    return ret

def isAdvancedSearch(request):
    """ Return True if advanced search is requested """
    try:
        return int(request.form['advancedsearch'][0])
    except KeyError:
        return False


def searchHints(f, hints):
    """ Return a paragraph showing hints for a search

    @param f: the formatter to use
    @param hints: list of hints (as strings) to show
    """
    return ''.join([
        f.paragraph(1, attr={'class': 'searchhint'}),
        # this is illegal formatter usage anyway, so we can directly use a literal
        "<br>".join(hints),
        f.paragraph(0),
    ])


def execute(pagename, request, fieldname='value', titlesearch=0, statistic=0):
    _ = request.getText
    titlesearch = checkTitleSearch(request)
    if titlesearch < 0:
        request.makeForbidden403()
        request.surge_protect(kick_him=True) # get rid of spammer
        return

    advancedsearch = isAdvancedSearch(request)

    # context is relevant only for full search
    if titlesearch:
        context = 0
    elif advancedsearch:
        context = 180 # XXX: hardcoded context count for advancedsearch
    else:
        context = int(request.form.get('context', [0])[0])

    # Get other form parameters
    needle = request.form.get(fieldname, [''])[0]
    case = int(request.form.get('case', [0])[0])
    regex = int(request.form.get('regex', [0])[0]) # no interface currently
    hitsFrom = int(request.form.get('from', [0])[0])
    mtime = None
    msg = ''
    historysearch = 0

    # if advanced search is enabled we construct our own search query
    if advancedsearch:
        and_terms = request.form.get('and_terms', [''])[0].strip()
        or_terms = request.form.get('or_terms', [''])[0].strip()
        not_terms = request.form.get('not_terms', [''])[0].strip()
        #xor_terms = request.form.get('xor_terms', [''])[0].strip()
        categories = request.form.get('categories', [''])
        timeframe = request.form.get('time', [''])[0].strip()
        language = request.form.get('language', [''])
        mimetype = request.form.get('mimetype', [0])
        excludeunderlay = request.form.get('excludeunderlay', [0])[0]
        nosystemitems = request.form.get('nosystemitems', [0])[0]
        historysearch = request.form.get('historysearch', [0])[0]

        mtime = request.form.get('mtime', [''])[0]
        if mtime:
            mtime_parsed = None

            # get mtime from known date/time formats
            for fmt in (request.user.datetime_fmt,
                    request.cfg.datetime_fmt, request.user.date_fmt,
                    request.cfg.date_fmt):
                try:
                    mtime_parsed = time.strptime(mtime, fmt)
                except ValueError:
                    continue
                else:
                    break

            if mtime_parsed:
                mtime = time.mktime(mtime_parsed)
            else:
                # didn't work, let's try parsedatetime
                cal = Calendar()
                mtime_parsed, invalid_flag = cal.parse(mtime)
                # XXX it is unclear if usage of localtime here and in parsedatetime module is correct.
                # time.localtime is the SERVER's local time and of no relevance to the user (being
                # somewhere in the world)
                # mktime is reverse function for localtime, so this maybe fixes it again!?
                if not invalid_flag and mtime_parsed <= time.localtime():
                    mtime = time.mktime(mtime_parsed)
                else:
                    mtime_parsed = None # we don't use invalid stuff

            # show info
            if mtime_parsed:
                # XXX mtime_msg is not shown in some cases
                mtime_msg = _("(!) Only pages changed since '''%s''' are being displayed!",
                              wiki=True) % request.user.getFormattedDateTime(mtime)
            else:
                mtime_msg = _('/!\\ The modification date you entered was not '
                        'recognized and is therefore not considered for the '
                        'search results!', wiki=True)
        else:
            mtime_msg = None

        word_re = re.compile(r'(\"[\w\s]+"|\w+)')
        needle = ''
        if categories[0]:
            needle += 'category:%s ' % ','.join(categories)
        if language[0]:
            needle += 'language:%s ' % ','.join(language)
        if mimetype[0]:
            needle += 'mimetype:%s ' % ','.join(mimetype)
        if excludeunderlay:
            needle += '-domain:underlay '
        if nosystemitems:
            needle += '-domain:system '
        if and_terms:
            needle += '(%s) ' % and_terms
        if not_terms:
            needle += '(%s) ' % ' '.join(['-%s' % t for t in word_re.findall(not_terms)])
        if or_terms:
            needle += '(%s) ' % ' or '.join(word_re.findall(or_terms))

    # check for sensible search term
    stripped = needle.strip()
    if len(stripped) == 0:
        request.theme.add_msg(_('Please use a more selective search term instead '
                'of {{{"%s"}}}', wiki=True) % wikiutil.escape(needle), "error")
        Page(request, pagename).send_page()
        return
    needle = stripped

    # Setup for type of search
    if titlesearch:
        title = _('Title Search: "%s"')
        sort = 'page_name'
    else:
        if advancedsearch:
            title = _('Advanced Search: "%s"')
        else:
            title = _('Full Text Search: "%s"')
        sort = 'weight'

    # search the pages
    from MoinMoin.search import searchPages, QueryParser, QueryError
    try:
        query = QueryParser(case=case, regex=regex,
                titlesearch=titlesearch).parse_query(needle)
    except QueryError: # catch errors in the search query
        request.theme.add_msg(_('Your search query {{{"%s"}}} is invalid. Please refer to '
                'HelpOnSearching for more information.', wiki=True, percent=True) % wikiutil.escape(needle), "error")
        Page(request, pagename).send_page()
        return

    results = searchPages(request, query, sort, mtime, historysearch)

    # directly show a single hit for title searches
    # this is the "quick jump" functionality if you don't remember
    # the pagename exactly, but just some parts of it
    if titlesearch and len(results.hits) == 1:
        page = results.hits[0]
        if not page.attachment: # we did not find an attachment
            page = Page(request, page.page_name)
            highlight = query.highlight_re()
            if highlight:
                querydict = {'highlight': highlight}
            else:
                querydict = {}
            url = page.url(request, querystr=querydict)
            request.http_redirect(url)
            return
    if not results.hits: # no hits?
        f = request.formatter
        querydict = wikiutil.parseQueryString(request.query_string)
        querydict.update({'titlesearch': 0})

        request.theme.add_msg(_('Your search query {{{"%s"}}} didn\'t return any results. '
                'Please change some terms and refer to HelpOnSearching for '
                'more information.%s', wiki=True, percent=True) % (wikiutil.escape(needle),
                    titlesearch and ''.join([
                        '<br>',
                        _('(!) Consider performing a', wiki=True), ' ',
                        f.url(1, href=request.page.url(request, querydict, escape=0)),
                        _('full-text search with your search terms'),
                        f.url(0), '.',
                    ]) or ''), "error")
        Page(request, pagename).send_page()
        return

    request.emit_http_headers()

    # This action generates data using the user language
    request.setContentLanguage(request.lang)

    request.theme.send_title(title % needle, form=request.form, pagename=pagename)

    # Start content (important for RTL support)
    request.write(request.formatter.startContent("content"))

    # Hints
    f = request.formatter
    hints = []

    if titlesearch:
        querydict = wikiutil.parseQueryString(request.query_string)
        querydict.update({'titlesearch': 0})

        hints.append(''.join([
            _("(!) You're performing a title search that might not include"
                ' all related results of your search query in this wiki. <<BR>>', wiki=True),
            ' ',
            f.url(1, href=request.page.url(request, querydict, escape=0)),
            f.text(_('Click here to perform a full-text search with your '
                'search terms!')),
            f.url(0),
        ]))

    if advancedsearch and mtime_msg:
        hints.append(mtime_msg)

    if hints:
        request.write(searchHints(f, hints))

    # Search stats
    request.write(results.stats(request, request.formatter, hitsFrom))

    # Then search results
    info = not titlesearch
    if context:
        output = results.pageListWithContext(request, request.formatter,
                info=info, context=context, hitsFrom=hitsFrom, hitsInfo=1)
    else:
        output = results.pageList(request, request.formatter, info=info,
                hitsFrom=hitsFrom, hitsInfo=1)

    request.write(output)

    request.write(request.formatter.endContent())
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

