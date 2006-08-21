# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - fullsearch action

    This is the backend of the search form. Search pages and print results.
    
    @copyright: 2001 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import re, time
from MoinMoin.Page import Page
from MoinMoin import wikiutil
from MoinMoin.support.parsedatetime.parsedatetime import Calendar


def isTitleSearch(request):
    """ Return True for title search, False for full text search 
    
    When used in FullSearch macro, we have 'titlesearch' parameter with
    '0' or '1'. In standard search, we have either 'titlesearch' or
    'fullsearch' with localized string. If both missing, default to
    True (might happen with Safari).
    """
    try:
        return int(request.form['titlesearch'][0])
    except ValueError:
        return True
    except KeyError:
        return 'fullsearch' not in request.form and \
                not isAdvancedSearch(request)

def isAdvancedSearch(request):
    try:
        return int(request.form['advancedsearch'][0])
    except KeyError:
        return False

def execute(pagename, request, fieldname='value', titlesearch=0):
    _ = request.getText
    titlesearch = isTitleSearch(request)
    advancedsearch = isAdvancedSearch(request)

    # context is relevant only for full search
    if titlesearch:
        context = 0
    elif advancedsearch:
        # XXX: hardcoded
        context = 180
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

    max_context = 1 # only show first `max_context` contexts XXX still unused

    if advancedsearch:
        and_terms = request.form.get('and_terms', [''])[0].strip()
        or_terms = request.form.get('or_terms', [''])[0].strip()
        not_terms = request.form.get('not_terms', [''])[0].strip()
        #xor_terms = request.form.get('xor_terms', [''])[0].strip()
        categories = request.form.get('categories', [''])[0].strip()
        timeframe = request.form.get('time', [''])[0].strip()
        language = request.form.get('language',
                [request.cfg.language_default])[0]
        mimetype = request.form.get('mimetype', [0])[0]
        includeunderlay = request.form.get('includeunderlay', [0])[0]
        nosystempages = request.form.get('nosystempages', [0])[0]
        historysearch = request.form.get('historysearch', [0])[0]

        mtime = request.form.get('mtime', [None])[0]
        if mtime:
            cal = Calendar()
            mtime_parsed = cal.parse(mtime)

            if mtime_parsed[1] == 0 and mtime_parsed[0] <= time.localtime():
                mtime = time.mktime(mtime_parsed[0])
            else:
                msg = _('The modification date you entered was not recognized '
                        'and is therefore not considered for the search '
                        'results!')
                mtime = None
        
        word_re = re.compile(r'(\"[\w\s]+"|\w+)')
        needle = ''
        if language:
            needle += 'language:%s ' % language
        if mimetype:
            needle += 'mimetype:%s ' % mimetype
        if not includeunderlay:
            needle += '-domain:underlay '
        if nosystempages:
            needle += '-domain:system '
        if categories:
            needle += '(%s) ' % ' or '.join(['category:%s' % cat
                for cat in word_re.findall(categories)])
        if and_terms:
            needle += '(%s) ' % and_terms
        if not_terms:
            needle += '(%s) ' % ' '.join(['-%s' % t for t in word_re.findall(not_terms)])
        if or_terms:
            needle += '(%s) ' % ' or '.join(word_re.findall(or_terms))

    # check for sensible search term
    stripped = needle.strip()
    if len(stripped) == 0:
        err = _('Please use a more selective search term instead '
                'of {{{"%s"}}}') % needle
        Page(request, pagename).send_page(request, msg=err)
        return
    needle = stripped

    # Setup for type of search
    if titlesearch:
        title = _('Title Search: "%s"')
        sort = 'page_name'
    else:
        title = _('Full Text Search: "%s"')
        sort = 'weight'

    # search the pages
    from MoinMoin.search import searchPages, QueryParser
    #try:
    query = QueryParser(case=case, regex=regex,
                titlesearch=titlesearch).parse_query(needle)
    results = searchPages(request, query, sort, mtime, historysearch)
    #except ValueError:
    #    err = _('Your search query {{{"%s"}}} is invalid. Please refer to '
    #            'HelpOnSearching for more information.') % needle
    #    Page(request, pagename).send_page(request, msg=err)
    #    return

    # directly show a single hit
    # XXX won't work with attachment search
    # improve if we have one...
    if len(results.hits) == 1:
        page = results.hits[0]
        if not page.attachment: # we did not find an attachment
            page = Page(request, page.page_name)
            url = page.url(request, querystr={'highlight': query.highlight_re()}, escape=0, relative=False)
            request.http_redirect(url)
            return

    request.emit_http_headers()

    # This action generate data using the user language
    request.setContentLanguage(request.lang)

    request.theme.send_title(title % needle, form=request.form,
            pagename=pagename, msg=msg)

    # Start content (important for RTL support)
    request.write(request.formatter.startContent("content"))

    # Did we get any hits?
    if results.hits:
        # First search stats
        request.write(results.stats(request, request.formatter, hitsFrom))

        # Then search results
        info = not titlesearch
        if context:
            output = results.pageListWithContext(request, request.formatter,
                    info=info, context=context, hitsFrom=hitsFrom)
        else:
            output = results.pageList(request, request.formatter, info=info,
                    hitsFrom=hitsFrom)
        request.write(output)
    else:
        f = request.formatter
        request.write(''.join([
            f.heading(1, 3),
            f.text(_('Your search query didn\'t return any results.')),
            f.heading(0, 3),
        ]))

    request.write(request.formatter.endContent())
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

