# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - fullsearch action

    This is the backend of the search form. Search pages and print results.
    
    @copyright: 2001 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.Page import Page
from MoinMoin import wikiutil


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
        return 'fullsearch' not in request.form


def execute(pagename, request, fieldname='value', titlesearch=0):
    _ = request.getText
    titlesearch = isTitleSearch(request)

    # context is relevant only for full search
    if titlesearch:
        context = 0
    else:
        context = int(request.form.get('context', [0])[0])

    # Get other form parameters
    needle = request.form.get(fieldname, [''])[0]
    case = int(request.form.get('case', [0])[0])
    regex = int(request.form.get('regex', [0])[0]) # no interface currently
    hitsFrom = int(request.form.get('from', [0])[0])

    max_context = 1 # only show first `max_context` contexts XXX still unused

    # check for sensible search term
    striped = needle.strip()
    if len(striped) == 0:
        err = _('Please use a more selective search term instead '
                'of {{{"%s"}}}') % needle
        request.emit_http_headers()
        Page(request, pagename).send_page(request, msg=err)
        return

    # Setup for type of search
    if titlesearch:
        title = _('Title Search: "%s"')
        sort = 'page_name'
    else:
        title = _('Full Text Search: "%s"')
        sort = 'weight'

    # search the pages
    from MoinMoin.search import searchPages, QueryParser
    query = QueryParser(case=case, regex=regex,
            titlesearch=titlesearch).parse_query(needle)
    results = searchPages(request, query, sort)

    # directly show a single hit
    # XXX won't work with attachment search
    # improve if we have one...
    if len(results.hits) == 1:
        page = results.hits[0]
        if not page.attachment: # we did not find an attachment
            page = Page(request, page.page_name)
            # TODO: remove escape=0 in 2.0
            url = page.url(request, querystr={'highlight': query.highlight_re()},
                           escape=0)
            request.http_redirect(url)
            return

    request.emit_http_headers()

    # This action generate data using the user language
    request.setContentLanguage(request.lang)

    request.theme.send_title(title % needle, form=request.form, pagename=pagename)

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

